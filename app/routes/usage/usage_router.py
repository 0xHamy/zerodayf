from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os, aiofiles
from pathlib import Path
import app

usage_router = APIRouter(prefix="/usage", tags=["Usage"])


class DocItem(BaseModel):
    filename: str
    title: str

class DocsListResponse(BaseModel):
    docs: List[DocItem]

class DocContentResponse(BaseModel):
    content: str

class ErrorResponse(BaseModel):
    detail: str


DOCS_DIR = Path(app.__file__).resolve().parent / "docs"


@usage_router.get("/docs", response_model=DocsListResponse)
async def list_docs():
    """
    Retrieves a list of all available Markdown documentation files in sorted order.
    """
    try:
        files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".md")]
        
        def extract_order(filename: str) -> int:
            try:
                return int(filename.split('_')[0])
            except (IndexError, ValueError):
                return float('inf') 
        
        sorted_files = sorted(files, key=extract_order)
        docs = [
            DocItem(
                filename=f,
                title=os.path.splitext(f)[0].split('_', 1)[-1].replace('_', ' ').title()
            )
            for f in sorted_files
        ]
        
        return DocsListResponse(docs=docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@usage_router.get("/docs/{doc_name}", response_model=DocContentResponse)
async def get_doc(doc_name: str):
    """
    Retrieves the content of a specific Markdown documentation file.
    """
    safe_doc_name = os.path.basename(doc_name)
    file_path = os.path.join(DOCS_DIR, safe_doc_name)
    
    if not os.path.isfile(file_path) or not file_path.endswith(".md"):
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        return DocContentResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


