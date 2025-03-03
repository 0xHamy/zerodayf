from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, CodeMappings
from sqlalchemy import select
from datetime import datetime
from typing import List

code_map_router = APIRouter(prefix="/code-map", tags=["Code Map"])

@code_map_router.get("/mappings")
async def get_mappings(db: AsyncSession = Depends(get_db)):
    try:
        query = select(CodeMappings).order_by(CodeMappings.date.desc())
        result = await db.execute(query)
        mappings = result.scalars().all()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": [
                    {
                        "id": m.id,
                        "endpoint": m.endpoint,
                        "code_file_paths": m.code_file_paths,
                        "date": m.date.isoformat(),
                        "scan_status": "completed"
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

@code_map_router.delete("/mappings")
async def delete_mappings(mapping_ids: dict, db: AsyncSession = Depends(get_db)):
    try:
        ids = mapping_ids.get('mapping_ids', [])
        query = select(CodeMappings).where(CodeMappings.id.in_(ids))
        results = await db.execute(query)
        mappings = results.scalars().all()
        
        for mapping in mappings:
            await db.delete(mapping)
        await db.commit()
        
        return JSONResponse(
            status_code=200,
            content={"status": "success"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@code_map_router.get("/mappings/{mapping_id}")
async def get_mapping_by_id(mapping_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = select(CodeMappings).where(CodeMappings.id == mapping_id)
        result = await db.execute(query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Mapping not found"}
            )
            
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "id": mapping.id,
                    "endpoint": mapping.endpoint,
                    "code_file_paths": mapping.code_file_paths,
                    "date": mapping.date.isoformat()
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


