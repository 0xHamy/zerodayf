from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, EndpointMappings, AnalysisTemplates
from fastapi import HTTPException
from sqlalchemy import select
from datetime import datetime
import json, html
from pydantic import BaseModel, Json

endpoint_map_router = APIRouter(prefix="/endpoint-map", tags=["Endpoint Mapping"])

# For displaying all mappings 
@endpoint_map_router.get("/mappings")
async def get_mappings(db: AsyncSession = Depends(get_db)):
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


# For selecting individual mappings:
@endpoint_map_router.get("/select-mapping")
async def select_mapping(db: AsyncSession = Depends(get_db)):
    try:
        query = select(EndpointMappings.id, EndpointMappings.name)
        result = await db.execute(query)
        mappings = result.all()
        return {"status": "success", "data": [{"id": m.id, "name": m.name} for m in mappings]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@endpoint_map_router.post("/mappings")
async def create_mapping(mapping: MappingCreate, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(e)}
        )


@endpoint_map_router.delete("/mappings")
async def delete_mappings(mapping_ids: dict, db: AsyncSession = Depends(get_db)):
    try:
        ids = mapping_ids.get('mapping_ids', [])
        query = select(EndpointMappings).where(EndpointMappings.id.in_(ids))
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

@endpoint_map_router.get("/mappings/{mapping_id}")
async def get_mapping_by_id(mapping_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = select(EndpointMappings).where(EndpointMappings.id == mapping_id)
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
                    "name": mapping.name,
                    "data": mapping.data,
                    "date": mapping.date.isoformat()
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@endpoint_map_router.get("/mappings/{mapping_id}")
async def get_mapping_by_id(mapping_id: int, db: AsyncSession = Depends(get_db)):
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


@endpoint_map_router.get("/analysis-templates")
async def get_analysis_templates(db: AsyncSession = Depends(get_db)):
    try:
        query = select(AnalysisTemplates.id, AnalysisTemplates.name)
        result = await db.execute(query)
        templates = result.all()
        return {"status": "success", "data": [{"id": t.id, "name": t.name} for t in templates]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@endpoint_map_router.get("/file-contents")
async def get_file_contents(file_path: str, start_line: int = None, end_line: int = None):
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


