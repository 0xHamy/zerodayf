import asyncio, httpx, json, subprocess
from fastapi import HTTPException, Depends
from typing import Dict, Any, Union, List
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from app.models.database import SessionLocal
from app.models.database import AnalysisTemplates
from sqlalchemy import select, delete
from app.models.database import get_db, CodeScans, AsyncSession
from app.scanners.semgrep_scanner import scan_code_with_semgrep
from app.scanners.ai_scanner import send_request_to_provider
from datetime import datetime
import time


analysis_router = APIRouter(prefix="/analysis", tags=["Analysis Router"])


@analysis_router.get("/templates-by-type")
async def get_templates_by_type():
    async with SessionLocal() as db:
        try:
            result = await db.execute(
                select(AnalysisTemplates)
            )
            templates = result.scalars().all()

            if not templates:
                logger.info("No templates found")
                return JSONResponse(
                    status_code=404,
                    content={"message": "No templates found", "status": "error"}
                )

            template_data = [
                {"name": template.name, "template_type": template.template_type}
                for template in templates
            ]
            return {
                "status": "success",
                "data": template_data
            }

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Internal server error: {str(e)}", "status": "error"}
            )



@analysis_router.get("/code-scans")
async def get_code_scans(db: AsyncSession = Depends(get_db)):
    try:
        query = select(CodeScans)
        result = await db.execute(query)
        scans = result.scalars().all()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": [
                    {
                        "id": scan.id,
                        "scan_name": scan.scan_name,
                        "uid": scan.uid,
                        "scan_type": scan.scan_type,
                        "date": scan.date.isoformat(),
                    }
                    for scan in scans
                ]
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )



@analysis_router.delete("/code-scans")
async def delete_code_scans(payload: Dict = Body(...), db: AsyncSession = Depends(get_db)):
    try:
        scan_ids = payload.get('scan_ids', [])
        
        if not scan_ids:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "No scan IDs provided"}
            )

        query = select(CodeScans).where(CodeScans.id.in_(scan_ids))
        results = await db.execute(query)
        scans = results.scalars().all()

        for scan in scans:
            await db.delete(scan)
        await db.commit()

        if not scans:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "No scans found with provided IDs"}
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Successfully deleted {len(scans)} scan(s)"
            }
        )
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@analysis_router.post("/perform-analysis/semgrep")
async def semgrep_scan_route(scan_data: dict, db: AsyncSession = Depends(get_db)):
    try:
        files = scan_data.get("files", [])
        template_name = scan_data.get("template")

        if not files or not template_name:
            raise HTTPException(status_code=400, detail="Missing files or template")

        query = select(AnalysisTemplates).where(AnalysisTemplates.name == template_name)
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template or template.template_type != "semgrep":
            raise HTTPException(status_code=404, detail="Semgrep template not found or invalid type")

        codes_and_paths = []
        for file in files:
            full_path = file["path"]
            try:
                file_path, line_range = full_path.split('#')
                start_line, end_line = map(int, line_range.split('-')) if line_range else (None, None)
            except ValueError:
                start_line, end_line = None, None

            with open(file_path, 'r') as f:
                lines = f.readlines()

            code = ''.join(lines[start_line-1:end_line]) if start_line and end_line else ''.join(lines)
            codes_and_paths.append({"code": code, "path": full_path})

        scan_results = await scan_code_with_semgrep(codes_and_paths, template.data)

        timestamp = int(time.time())
        uid = f"semgrep_{timestamp}"
        scan_name = f"Scan_{template_name}_{timestamp}"
        scan_result_json = json.dumps(scan_results)

        new_scan = CodeScans(
            scan_name=scan_name,
            uid=uid,
            scan_type="semgrep",
            scan_template=template.data,
            scan_result=scan_result_json,
            date=datetime.now()
        )
        db.add(new_scan)
        await db.commit()

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Semgrep scan completed", "scan_uid": uid}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during Semgrep scan: {str(e)}")


@analysis_router.post("/perform-analysis/ai")
async def ai_scan_route(scan_data: dict, db: AsyncSession = Depends(get_db)):
    try:
        # Extract files and template name from the request
        files = scan_data.get("files", [])
        template_name = scan_data.get("template")

        if not files or not template_name:
            raise HTTPException(status_code=400, detail="Missing files or template")

        # Fetch the template from the database
        query = select(AnalysisTemplates).where(AnalysisTemplates.name == template_name)
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template or template.template_type != "ai":
            raise HTTPException(status_code=404, detail="AI template not found or invalid type")

        # Prepare code snippets with file paths
        code_snippets = []
        for file in files:
            full_path = file["path"]  # e.g., "/path/to/file#start-end"
            try:
                file_path, line_range = full_path.split('#')
                start_line, end_line = map(int, line_range.split('-')) if line_range else (None, None)
            except ValueError:
                start_line, end_line = None, None  # No line range provided

            # Read the file content
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
            except Exception as file_err:
                raise HTTPException(status_code=500, detail=f"Failed to read file {file_path}: {str(file_err)}")

            # Extract the code snippet based on line range
            if start_line and end_line:
                code = ''.join(lines[start_line-1:end_line])  # 0-based indexing
            else:
                code = ''.join(lines)  # Use full file if no range

            # Format the snippet with file path and code
            code_snippets.append(f"{full_path}\n{code}")

        # Combine snippets with three line breaks
        combined_code = "\n\n\n".join(code_snippets)
        populated_template = template.data.replace("CODEPLACEHOLDER", combined_code)

        # Perform AI scan
        scan_result = await send_request_to_provider(populated_template, db)
        
        # Generate a unique ID for the scan
        timestamp = int(time.time())
        uid = f"ai_{timestamp}"

        # Save the scan results to the database
        scan_name = f"Scan_{template_name}_{timestamp}"

        new_scan = CodeScans(
            scan_name=scan_name,
            uid=uid,
            scan_type="ai",
            scan_template=populated_template,
            scan_result=scan_result,
            date=datetime.now()
        )
        db.add(new_scan)
        await db.commit()

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "AI scan completed", "scan_uid": uid}
        )

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=f"Error during AI scan: {str(e)}")


@analysis_router.get("/debug-scans/{scan_id}")
async def debug_scans(scan_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = select(CodeScans).where(CodeScans.id == scan_id)
        result = await db.execute(query)
        scan = result.scalar_one_or_none()

        if not scan:
            raise HTTPException(status_code=404, detail=f"No scan found with id {scan_id}")

        return scan.scan_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

