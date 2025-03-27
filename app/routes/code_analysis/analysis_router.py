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
        query = select(CodeScans).order_by(CodeScans.date.desc())
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


