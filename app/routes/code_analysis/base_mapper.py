from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import json, os
from app.models.database import get_db, CodeMappings 
from app.mappers.flask_mapper import FlaskMapper
from app.mappers.laravel_mapper import LaravelMapper


base_mapper_router = APIRouter(prefix="/base-code-mapper", tags=["Base Code Mapper"])

mapper_classes = {
    "flask": FlaskMapper,
    "laravel": LaravelMapper,
}

# Define the PROCESS_MAPPING function so background_tasks.add_task(...) works!
async def process_mapping(framework: str, app_path: str, endpoints: List[str], db: AsyncSession):
    try:
        framework_key = framework.lower()
        if framework_key in mapper_classes:
            mapper = mapper_classes[framework_key](app_path)
        else:
            raise ValueError(f"Unsupported framework: {framework}")

        for endpoint in endpoints:
            print(f"[DEBUG] Processing endpoint: {endpoint}")
            result_dict = mapper.map_endpoint(endpoint)

            if result_dict:
                json_output = json.dumps(result_dict)
                mapping = CodeMappings(
                    endpoint=endpoint,
                    code_file_paths=json_output
                )
                db.add(mapping)
                await db.commit()
                print(f"[DEBUG] Saved mapping for {endpoint}: {json_output}")

    except Exception as e:
        print(f"[DEBUG] Error in process_mapping: {e}")
        await db.rollback()
        raise


@base_mapper_router.post("/start-mapping")
async def start_mapping(
    mapping_data: Dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        framework = mapping_data.get("framework")
        app_path = mapping_data.get("app_path")
        endpoints = mapping_data.get("endpoints", [])

        if not all([framework, app_path, endpoints]):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        if not os.path.exists(app_path):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Application path does not exist"}
            )

        background_tasks.add_task(
            process_mapping,
            framework,
            app_path,
            endpoints,
            db
        )

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Mapping process started"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
