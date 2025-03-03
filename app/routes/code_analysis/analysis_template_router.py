from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.models.database import SessionLocal, AnalysisTemplates
from datetime import datetime
from app.models.database import AnalysisTemplates, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse


template_analysis_router = APIRouter(prefix="/analysis-templates", tags=["Analysis Template"])


class TemplateBase(BaseModel):
    name: str = Field(..., description="Template name")
    data: str = Field(..., description="Template content")
    template_type: str = Field(..., description="Type of template (e.g., 'ai' or 'semgrep')")


class TemplateResponse(TemplateBase):
    id: int
    date: datetime


# DB Operations
async def get_template_by_name(db, name: str):
    """Helper function to get template by name"""
    result = await db.execute(
        select(AnalysisTemplates).where(AnalysisTemplates.name == name)
    )
    return result.scalars().first()


@template_analysis_router.get("/", response_model=List[TemplateResponse])
async def get_templates():
    """Get all templates"""
    async with SessionLocal() as db:
        result = await db.execute(select(AnalysisTemplates).order_by(AnalysisTemplates.date.desc()))
        return result.scalars().all()


@template_analysis_router.get("/{template_name}", response_model=TemplateResponse)
async def get_template(template_name: str):
    """Get a specific template by name"""
    async with SessionLocal() as db:
        if template := await get_template_by_name(db, template_name):
            return template
        raise HTTPException(status_code=404, detail="Template not found")


@template_analysis_router.post("/", response_model=TemplateResponse)
async def create_template(template: TemplateBase):
    """Create a new template"""
    async with SessionLocal() as db:
        if await get_template_by_name(db, template.name):
            raise HTTPException(status_code=400, detail="Template name already exists")
        
        new_template = AnalysisTemplates(**template.dict())
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        return new_template


@template_analysis_router.put("/{template_name}", response_model=TemplateResponse)
async def update_template(template_name: str, template: TemplateBase):
    """Update an existing template"""
    async with SessionLocal() as db:
        if existing := await get_template_by_name(db, template_name):
            for key, value in template.dict().items():
                setattr(existing, key, value)
            await db.commit()
            await db.refresh(existing)
            return existing
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")


@template_analysis_router.delete("/{template_name}")
async def delete_template(template_name: str):
    """Delete a template"""
    async with SessionLocal() as db:
        if template := await get_template_by_name(db, template_name):
            await db.delete(template)
            await db.commit()
            return {"message": "Template deleted successfully"}
        raise HTTPException(status_code=404, detail="Template not found")


@template_analysis_router.post("/load-defaults/{template_type}")
async def load_default_templates(template_type: str, db: AsyncSession = Depends(get_db)):
    """
    Populate the analysis_templates table with dummy data based on the template type.
    Args:
        template_type: The type of template to populate ('ai' or 'semgrep')
    """

    if template_type not in ["ai", "semgrep"]:
        return JSONResponse(
            status_code=200,  
            content={"status": "error", "message": "Invalid template_type. Must be 'ai' or 'semgrep'"}
        )

    # Define dummy data based on template type
    if template_type == "ai":
        dummy_data = [
            {
                "name": "default_ai",
                "data": """
### Perform vulnerability analysis on code

Analyze the following codes, tell me the 'possible' if any relation between them. Look for the vulnerabilities:
- XSS
- SSRF
- Code injection

CODEPLACEHOLDER
                """,
                "template_type": "ai"
            }
        ]
    elif template_type == "semgrep":
        dummy_data = [
            {
                "name": "default_semgrep",
                "data": """p/security-audit""",
                "template_type": "semgrep"
            }
        ]

    # Attempt to insert data
    try:
        async with SessionLocal() as session:
            for data in dummy_data:
                template = AnalysisTemplates(
                    name=data["name"],
                    data=data["data"],
                    template_type=data["template_type"]
                )
                session.add(template)
            await session.commit()
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Successfully added {data["name"]}."
                }
            )
    except Exception as e:
        await session.rollback()
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": f"Failed to add {template_type} templates: {str(e)}"}
        )


