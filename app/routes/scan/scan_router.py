from fastapi import APIRouter, HTTPException, BackgroundTasks, Response, Depends
from fastapi.responses import JSONResponse 
from pydantic import BaseModel
from typing import List
from app.models.database import SessionLocal, ScanTemplates, CodeScans, get_db, AsyncSession
from app.routes.scan.code_scan import perform_scan, list_scans
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.future import select 
from sqlalchemy import delete
import asyncio


scan_router = APIRouter(prefix="/scan", tags=["Scan"])


# Pydantic schema
class ScanTemplateRequest(BaseModel):
    name: str
    data: str

# Pydantic schema for returning a list or single
class ScanTemplateResponse(BaseModel):
    id: int
    name: str
    data: str

# Pydantic schema for scan requests
class ScanRequest(BaseModel):
    scan_name: str
    template_name: str
    code: str

# Pydantic schema for scan responses
class ScanResponse(BaseModel):
    scan_id: int
    message: str

# Pydantic schema for listing scans
class ScanListItem(BaseModel):
    id: int
    scan_name: str
    scan_template: str
    date: datetime
    status: str

# Pydantic schema for the list response
class ScanListResponse(BaseModel):
    scans: List[ScanListItem]

# Optional: Route to fetch scan results by scan_id
# TODO: I may not needs this at all, what am I even doing with this?
class ScanResultResponse(BaseModel):
    scan_id: int
    scan_name: str
    scan_template: str
    scan_result: str


@scan_router.get("/get-templates", response_model=List[ScanTemplateResponse])
async def get_templates():
    async with SessionLocal() as db:
        result = await db.execute(select(ScanTemplates))
        templates = result.scalars().all()
        return [
            ScanTemplateResponse(
                id=t.id,
                name=t.name,
                data=t.data,
                date=t.date
            )
            for t in templates
        ]

@scan_router.get("/get-template/{template_name}", response_model=ScanTemplateResponse)
async def get_template(template_name: str):
    async with SessionLocal() as db:
        # Query the database for the template with the given name
        result = await db.execute(
            select(ScanTemplates).where(ScanTemplates.name == template_name)
        )
        tmpl = result.scalars().first()
        
        if not tmpl:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return ScanTemplateResponse(
            id=tmpl.id,
            name=tmpl.name,
            data=tmpl.data,
            date=tmpl.date
        )

@scan_router.post("/create-template", response_model=ScanTemplateResponse)
async def create_template(req: ScanTemplateRequest):
    async with SessionLocal() as db:
        # Check if name exists
        existing = await db.execute(select(ScanTemplates).where(ScanTemplates.name == req.name))
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Name already exists")

        new_tmpl = ScanTemplates(name=req.name, data=req.data)
        db.add(new_tmpl)
        await db.commit()
        await db.refresh(new_tmpl)

        return ScanTemplateResponse(
            id=new_tmpl.id,
            name=new_tmpl.name,
            data=new_tmpl.data
        )


@scan_router.post("/update-template/{template_name}", response_model=ScanTemplateResponse)
async def update_template(template_name: str, req: ScanTemplateRequest):
    """
    Updates an existing scan template identified by its name.
    """
    async with SessionLocal() as db:
        tmpl = await db.execute(select(ScanTemplates).where(ScanTemplates.name == template_name))
        tmpl = tmpl.scalars().first()

        if not tmpl:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

        tmpl.name = req.name
        tmpl.data = req.data

        await db.commit()
        await db.refresh(tmpl)

        return ScanTemplateResponse(
            id=tmpl.id,
            name=tmpl.name,
            data=tmpl.data
        )



@scan_router.delete("/delete-template/{template_name}")
async def delete_template(template_name: str):
    async with SessionLocal() as db:
        stmt = select(ScanTemplates).where(ScanTemplates.name == template_name)
        result = await db.execute(stmt)
        tmpl = result.scalars().first()
        if not tmpl:
            raise HTTPException(status_code=404, detail="Template not found")
        await db.delete(tmpl)
        await db.commit()
        
        return {"message": "Template deleted successfully"}


###########################
# Code scanning operations
###########################

@scan_router.post("/start-scan", response_model=ScanResponse)
async def scan_code(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Initiates a scan by accepting a template name, scan name, and code.
    Runs the scan in the background and returns the scan ID.
    """
    async with SessionLocal() as db:
        result = await db.execute(
            select(ScanTemplates).where(ScanTemplates.name == request.template_name)
        )
        template = result.scalars().first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found.")

        new_scan = CodeScans(
            scan_name=request.scan_name,
            scan_template=template.data,
            scan_result="",
        )
        db.add(new_scan)
        await db.commit()
        await db.refresh(new_scan)

        scan_id = new_scan.id
        background_tasks.add_task(perform_scan, scan_id, request.template_name, request.code)
        
        return ScanResponse(scan_id=scan_id, message="Scan has been initiated and is running in the background.")



@scan_router.get("/get-result/{scan_id}", response_model=ScanResultResponse)
async def get_scan_result(scan_id: int):
    """
    Retrieves the result of a scan by its scan_id.
    """
    async with SessionLocal() as db:
        result = await db.execute(
            select(CodeScans).where(CodeScans.id == scan_id)
        )
        scan = result.scalars().first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found.")
        
        return ScanResultResponse(
            scan_id=scan.id,
            scan_name=scan.scan_name,
            scan_template=scan.scan_template,
            scan_result=scan.scan_result
        )


@scan_router.get("/list", response_model=ScanListResponse)
async def list_all_scans():
    """
    Retrieves a list of all scans with their current status (running or completed).
    """
    scans = await list_scans()
    scan_items = [ScanListItem(**scan) for scan in scans]
    return ScanListResponse(scans=scan_items)



@scan_router.get("/download-report/{scan_name}")
async def download_scan(scan_name: str):
    async with SessionLocal() as db:
        try:
            result = await db.execute(
                select(CodeScans).where(func.lower(CodeScans.scan_name) == func.lower(scan_name))
            )
            scan = result.scalars().first()
            
            if not scan:
                return JSONResponse(
                    status_code=404,
                    content={"message": "Scan name not found"}
                )
            if not scan.scan_result:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Scan result is empty"}
                )
            proc = await asyncio.create_subprocess_exec(
                'pandoc',
                '-f', 'html',
                '-t', 'pdf',
                '-o', '-',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            input_content = scan.scan_result.encode()
            stdout, stderr = await proc.communicate(input=input_content)
            
            if proc.returncode != 0:
                error_msg = stderr.decode()
                return JSONResponse(
                    status_code=500,
                    content={"message": f"PDF conversion failed: {error_msg}"}
                )

            if not stdout:
                return JSONResponse(
                    status_code=500,
                    content={"message": "Generated PDF is empty"}
                )

            return Response(
                content=stdout,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{scan_name}.pdf"'}
            )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Internal server error: {str(e)}"}
            )


@scan_router.get("/_scan-result/{scan_name}")
async def get_scan_result(scan_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CodeScans).where(CodeScans.scan_name == scan_name))
    scan = result.scalars().first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "scan_name": scan.scan_name,
        "scan_result": scan.scan_result
    }
