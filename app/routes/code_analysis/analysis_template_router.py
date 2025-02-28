from fastapi import APIRouter, HTTPException
from typing import List
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.models.database import SessionLocal, AnalysisTemplates
from datetime import datetime


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
        result = await db.execute(select(AnalysisTemplates))
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

