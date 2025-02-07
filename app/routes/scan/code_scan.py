import asyncio
from sqlalchemy.future import select
from sqlalchemy import update
from fastapi import HTTPException
from app.models.database import SessionLocal, APIKey, ScanTemplates, CodeScans
from datetime import datetime
from typing import Optional, List, Dict
from huggingface_hub import InferenceClient 
import httpx, markdown, re 
from bs4 import BeautifulSoup


async def get_active_api(db) -> Optional[APIKey]:
    """
    Retrieves the active API key from the database.
    Assumes only one API is active at any time.
    """
    result = await db.execute(select(APIKey).where(APIKey.is_active == True))
    active_api = result.scalars().first()
    return active_api


async def get_template(db, template_name: str) -> Optional[ScanTemplates]:
    """
    Retrieves a scan template by name.
    """
    result = await db.execute(select(ScanTemplates).where(ScanTemplates.name == template_name))
    template = result.scalars().first()
    return template


def populate_template(template_data: str, code: str) -> str:
    """
    Populates the template with the provided code by replacing the placeholder.
    Assumes that the placeholder 'CODE_PLACEHOLDER_HERE' is present in the template.
    """
    return template_data.replace("CODE_PLACEHOLDER_HERE", code)


def convert_markdown_html(md_text: str) -> str:
    extensions = [
        'fenced_code',      # For code blocks with language specification
        'codehilite',       # Syntax highlighting for code
        'tables',           # Support for tables
        'sane_lists',       # Better list handling
        'smarty',           # Smart quotes and dashes
        'toc'               # Table of contents
    ]
    
    extension_configs = {
        'codehilite': {
            'linenums': False,
            'use_pygments': True
        },
        'toc': {
            'permalink': False
        }
    }
    
    return markdown.markdown(
        md_text,
        extensions=extensions,
        extension_configs=extension_configs
    )


async def send_request_to_provider(provider: str, api_key: str, model: str, content: str) -> str:
    """
    Sends the populated template content to the appropriate API provider.
    Currently supports Hugging Face and OpenAI as examples.
    """
    provider = provider.lower()
    if provider == "huggingface":
        client = InferenceClient(api_key=api_key)
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=5000
            )
            return completion.choices[0].message['content']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Hugging Face API error: {str(e)}")
    
    elif provider == "openai":
        client = OpenAI(api_key=api_key)
        messages = [
            {
                "role": "user", 
                "content": content
            }
        ]
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=5000
            )
            return completion.choices[0].message['content']
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")


async def perform_scan(scan_id: int, template_name: str, code: str):
    async with SessionLocal() as db:
        # 1) Retrieve active API
        active_api = await get_active_api(db)
        if not active_api:
            await db.execute(
                update(CodeScans)
                .where(CodeScans.id == scan_id)
                .values(scan_result="Error: No active API found.")
            )
            await db.commit()
            return

        # 2) Retrieve the template
        template = await get_template(db, template_name)
        if not template:
            await db.execute(
                update(CodeScans)
                .where(CodeScans.id == scan_id)
                .values(scan_result="Error: Template not found.")
            )
            await db.commit()
            return

        # 3) Populate the template with user code
        try:
            populated_content = populate_template(template.data, code)
        except Exception as e:
            await db.execute(
                update(CodeScans)
                .where(CodeScans.id == scan_id)
                .values(scan_result=f"Error populating template: {str(e)}")
            )
            await db.commit()
            return

        # 4) Send request to provider (AI model)
        try:
            response = await send_request_to_provider(
                provider=active_api.provider,
                api_key=active_api.token,
                model=active_api.model,
                content=populated_content
            )
        except HTTPException as he:
            await db.execute(
                update(CodeScans)
                .where(CodeScans.id == scan_id)
                .values(scan_result=f"Error communicating with API provider: {he.detail}")
            )
            await db.commit()
            return
        except Exception as e:
            await db.execute(
                update(CodeScans)
                .where(CodeScans.id == scan_id)
                .values(scan_result=f"Unexpected error: {str(e)}")
            )
            await db.commit()
            return

        # 5) Convert AI's Markdown to HTML and save
        converted_html = convert_markdown_html(response)

        await db.execute(
            update(CodeScans)
            .where(CodeScans.id == scan_id)
            .values(scan_result=converted_html)
        )
        await db.commit()



async def list_scans() -> List[Dict]:
    """
    Retrieves all scans from the database and determines their status.
    Returns a list of dictionaries with scan details and status.
    """
    async with SessionLocal() as db:
        result = await db.execute(select(CodeScans).order_by(CodeScans.date.desc()))
        scans = result.scalars().all()
        
        scan_list = []
        for scan in scans:
            status = "completed" if scan.scan_result else "running"
            scan_list.append({
                "id": scan.id,
                "scan_name": scan.scan_name,
                "scan_template": scan.scan_template,
                "date": scan.date,
                "status": status
            })
        
        return scan_list
