from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, EndpointMappings, AnalysisTemplates, CodeScans, APIKey
from sqlalchemy import select
from datetime import datetime
import json, time, openai
from pydantic import BaseModel, Json
from threading import Thread
import asyncio
from typing import List, Dict, Any, Union
import subprocess
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from huggingface_hub import InferenceClient

endpoint_map_router = APIRouter(prefix="/endpoint-map", tags=["Endpoint Mapping"])

# --- Mappings Endpoints ---

@endpoint_map_router.get("/mappings")
async def get_mappings(db: AsyncSession = Depends(get_db)):
    """Retrieve all endpoint mappings ordered by date descending."""
    try:
        query = select(EndpointMappings).order_by(EndpointMappings.date.desc())
        result = await db.execute(query)
        mappings = result.scalars().all()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "data": m.data,
                        "date": m.date.isoformat()
                    }
                    for m in mappings
                ]
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


class MappingCreate(BaseModel):
    name: str
    data: Json


@endpoint_map_router.get("/select-mapping")
async def select_mapping(db: AsyncSession = Depends(get_db)):
    """Retrieve mapping IDs and names for selection."""
    try:
        query = select(EndpointMappings.id, EndpointMappings.name)
        result = await db.execute(query)
        mappings = result.all()
        return {"status": "success", "data": [{"id": m.id, "name": m.name} for m in mappings]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@endpoint_map_router.post("/mappings")
async def create_mapping(mapping: MappingCreate, db: AsyncSession = Depends(get_db)):
    """Create a new endpoint mapping."""
    try:
        new_mapping = EndpointMappings(
            name=mapping.name,
            data=json.dumps(mapping.data)
        )
        db.add(new_mapping)
        await db.commit()
        await db.refresh(new_mapping)
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "data": {"id": new_mapping.id},
                "message": "Mapping created successfully"
            }
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})


@endpoint_map_router.delete("/mappings")
async def delete_mappings(mapping_ids: dict, db: AsyncSession = Depends(get_db)):
    """Delete mappings by their IDs."""
    try:
        ids = mapping_ids.get('mapping_ids', [])
        query = select(EndpointMappings).where(EndpointMappings.id.in_(ids))
        results = await db.execute(query)
        mappings = results.scalars().all()
        for mapping in mappings:
            await db.delete(mapping)
        await db.commit()
        return JSONResponse(status_code=200, content={"status": "success"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@endpoint_map_router.get("/mappings/{mapping_id}")
async def get_mapping_by_id(mapping_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific mapping by its ID."""
    try:
        query = select(EndpointMappings).where(EndpointMappings.id == mapping_id)
        result = await db.execute(query)
        mapping = result.scalar_one_or_none()
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return {
            "status": "success",
            "data": {
                "id": mapping.id,
                "name": mapping.name,
                "data": mapping.data,
                "date": mapping.date.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Analysis Templates Endpoint ---

@endpoint_map_router.get("/analysis-templates")
async def get_analysis_templates(db: AsyncSession = Depends(get_db)):
    """Retrieve analysis templates with ID, name, and type."""
    try:
        query = select(AnalysisTemplates.id, AnalysisTemplates.name, AnalysisTemplates.template_type)
        result = await db.execute(query)
        templates = result.all()
        return {
            "status": "success",
            "data": [{"id": t.id, "name": t.name, "type": t.template_type} for t in templates]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- File Contents Endpoint ---

@endpoint_map_router.get("/file-contents")
async def get_file_contents(file_path: str, start_line: int = None, end_line: int = None):
    """Retrieve file contents with optional line range and total line count."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            total_lines = content.count('\n') + 1
            return {
                "status": "success",
                "data": {
                    "content": content,
                    "start_line": start_line if start_line is not None else 1,
                    "end_line": end_line if end_line is not None else total_lines
                }
            }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Helper Functions ---

async def fetch_file_contents(file_path: str, start_line: int = None, end_line: int = None):
    """Fetch file contents, optionally filtered by line range."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        if start_line and end_line:
            return ''.join(lines[start_line-1:end_line])
        return ''.join(lines)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File {file_path} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Scan Functions ---

async def run_semgrep_scan(scan_data, template_data, db: AsyncSession):
    """Run Semgrep scan on provided code snippets and save results."""
    codes_and_paths = []
    for file in scan_data["files"]:
        full_path = file["path"]
        file_path, line_range = full_path.split('#') if '#' in full_path else (full_path, None)
        start_line, end_line = map(int, line_range.split('-')) if line_range else (None, None)
        code = await fetch_file_contents(file_path, start_line, end_line)
        codes_and_paths.append({"code": code, "path": full_path})
    scan_results = await scan_code_with_semgrep(codes_and_paths, template_data)
    timestamp = int(time.time())
    uid = f"semgrep_{timestamp}"
    new_scan = CodeScans(
        scan_name=scan_data["scan_name"],
        uid=uid,
        scan_type="semgrep",
        scan_template=template_data,
        scan_result=json.dumps(scan_results),
        date=datetime.now()
    )
    db.add(new_scan)
    await db.commit()


async def run_ai_scan(scan_data, template_data, db: AsyncSession):
    """Run AI scan by sending populated template to the provider and save results."""
    code_snippets = []
    for file in scan_data["files"]:
        full_path = file["path"]
        file_path, line_range = full_path.split('#') if '#' in full_path else (full_path, None)
        start_line, end_line = map(int, line_range.split('-')) if line_range else (None, None)
        code = await fetch_file_contents(file_path, start_line, end_line)
        code_snippets.append(f"{full_path}\n```\n{code}\n```")
    combined_code = "\n\n".join(code_snippets)
    populated_template = template_data.replace("CODEPLACEHOLDER", combined_code)
    scan_result = await send_request_to_provider(populated_template, db)
    timestamp = int(time.time())
    uid = f"ai_{timestamp}"
    new_scan = CodeScans(
        scan_name=scan_data["scan_name"],
        uid=uid,
        scan_type="ai",
        scan_template=populated_template,
        scan_result=scan_result,
        date=datetime.now()
    )
    db.add(new_scan)
    await db.commit()


# --- Scan Routes ---

@endpoint_map_router.post("/perform-analysis/semgrep")
async def semgrep_scan_route(scan_data: dict, db: AsyncSession = Depends(get_db)):
    """Initiate a Semgrep scan in the background."""
    try:
        scan_name = scan_data.get("scan_name")
        files = scan_data.get("files", [])
        template_id = scan_data.get("template")
        if not files or not template_id:
            raise HTTPException(status_code=400, detail="Missing files or template")
        query = select(AnalysisTemplates).where(AnalysisTemplates.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        if not template or template.template_type != "semgrep":
            raise HTTPException(status_code=404, detail="Semgrep template not found or invalid type")
        Thread(target=lambda: asyncio.run(run_semgrep_scan(scan_data, template.data, db))).start()
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Semgrep scan initiated"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating Semgrep scan: {str(e)}")


import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@endpoint_map_router.post("/perform-analysis/ai")
async def ai_scan_route(scan_data: dict, db: AsyncSession = Depends(get_db)):
    """Initiate an AI scan in the background."""
    try:
        scan_name = scan_data.get("scan_name")
        files = scan_data.get("files", [])
        template_id = int(scan_data.get("template"))  # Convert string to integer
        if not files or not template_id:
            raise HTTPException(status_code=400, detail="Missing files or template")
        query = select(AnalysisTemplates).where(AnalysisTemplates.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        if not template or template.template_type != "ai":
            raise HTTPException(status_code=404, detail="AI template not found or invalid type")
        Thread(target=lambda: asyncio.run(run_ai_scan(scan_data, template.data, db))).start()
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "AI scan initiated"}
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID: must be an integer")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating AI scan: {str(e)}")


# --- Provider and Semgrep Functions ---

async def send_request_to_provider(content: str, db: AsyncSession = Depends(get_db)) -> str:
    """Send the populated template content to the appropriate API provider using the active API key."""
    query = select(APIKey).where(APIKey.is_active == True)
    result = await db.execute(query)
    active_key = result.scalar_one_or_none()
    if not active_key:
        raise HTTPException(status_code=400, detail="No active API key found")

    provider = active_key.provider.lower()
    api_key = active_key.token
    model = active_key.model
    max_tokens = active_key.max_tokens

    if provider == "huggingface":
        client = InferenceClient(api_key=api_key)
        messages = [{"role": "user", "content": content}]
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            return completion.choices[0].message['content']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Hugging Face API error: {str(e)}")

    elif provider == "openai":
        client = openai.Client(api_key=api_key)
        messages = [{"role": "user", "content": content}]
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=1
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    elif provider == "anthropic":
        client = Anthropic(api_key=api_key)
        messages = [{"role": "user", "content": content}]
        try:
            completion = await asyncio.to_thread(
                client.messages.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=1
            )
            return completion.content[0].text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")


async def scan_code_with_semgrep(codes_and_paths: List[Dict[str, str]], rules: Union[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """Run Semgrep scans on multiple code snippets and return simplified results."""
    try:
        if isinstance(rules, list):
            config_args = []
            for rule in rules:
                config_args.extend(["--config", rule])
        else:
            config_args = ["--config", rules]
        base_cmd = ["semgrep", *config_args, "--json", "-"]

        def run_semgrep(code: str):
            process = subprocess.Popen(
                base_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(code.encode('utf-8'))
            return stdout, stderr, process.returncode

        async def process_single_code(entry: Dict[str, str]) -> List[Dict[str, Any]]:
            code = entry["code"]
            path = entry["path"]
            with ThreadPoolExecutor() as executor:
                stdout, stderr, returncode = await asyncio.get_event_loop().run_in_executor(
                    executor, lambda: run_semgrep(code)
                )
            if stdout:
                try:
                    full_results = json.loads(stdout.decode('utf-8'))
                    simplified_results = []
                    for result in full_results.get("results", []):
                        simplified_result = {
                            "path": path,
                            "code": code.strip(),
                            "severity": result.get("extra", {}).get("severity", ""),
                            "impact": result.get("extra", {}).get("metadata", {}).get("impact", ""),
                            "message": result.get("extra", {}).get("message", ""),
                            "cwe": result.get("extra", {}).get("metadata", {}).get("cwe", [])
                        }
                        simplified_results.append(simplified_result)
                    if not simplified_results:
                        simplified_results.append({
                            "path": path,
                            "code": code.strip(),
                            "severity": "",
                            "impact": "",
                            "message": "No issues detected",
                            "cwe": []
                        })
                    return simplified_results
                except json.JSONDecodeError:
                    return [{"path": path, "code": code.strip(), "error": "Failed to parse Semgrep output"}]
            else:
                stderr_text = stderr.decode('utf-8') if stderr else "No error message provided"
                return [{"path": path, "code": code.strip(), "error": f"Semgrep failed: {stderr_text}"}]

        tasks = [process_single_code(entry) for entry in codes_and_paths]
        results_per_code = await asyncio.gather(*tasks, return_exceptions=True)

        combined_results = []
        for result in results_per_code:
            if isinstance(result, list):
                combined_results.extend(result)
            elif isinstance(result, Exception):
                combined_results.append({"path": "unknown", "code": "unknown", "error": str(result)})

        return {"results": combined_results}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error running Semgrep scans: {str(e)}")

