from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, EndpointMappings
from sqlalchemy import select
from datetime import datetime
import json

endpoint_map_router = APIRouter(prefix="/endpoint-map", tags=["Endpoint Mapping"])

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
                        "data": m.data,  # This is JSON string
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

@endpoint_map_router.post("/mappings")
async def create_mapping(mapping: dict, db: AsyncSession = Depends(get_db)):
    try:
        # Validate JSON data
        json_data = json.loads(mapping['data'])
        
        new_mapping = EndpointMappings(
            name=mapping['name'],
            data=json.dumps({
                "framework": mapping['framework'],
                "data": json_data
            })
        )
        db.add(new_mapping)
        await db.commit()
        await db.refresh(new_mapping)
        return JSONResponse(
            status_code=201,
            content={"status": "success", "id": new_mapping.id}
        )
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid JSON data"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
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

