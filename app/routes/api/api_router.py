from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from app.models.database import SessionLocal, APIKey
from app.manage_api.api_manage import check_api
from sqlalchemy.future import select 
from sqlalchemy import update, delete


api_router = APIRouter(prefix="/api", tags=["API"])


class APIValidationRequest(BaseModel):
    name: str
    provider: str
    token: str
    max_tokens: int
    model: str | None = None  


@api_router.post("/check-api")
async def validate_api_credentials(request: APIValidationRequest):
    check_result = check_api( 
        provider=request.provider,
        token=request.token,
        max_tokens=request.max_tokens,
        model_name=request.model or ""
    )

    if check_result["valid"]:
        return {
            "valid": True,
            "provider": request.provider,
            "message": "API key is valid. Please save to proceed."
        }
    else:
        return {
            "valid": False,
            "provider": request.provider,
            "message": f"Error: Invalid API key. {check_result['message']}"
        }



@api_router.post("/save-api")
async def save_api(request: APIValidationRequest):
    async with SessionLocal() as db:
        try:
            result = await db.execute(
                select(APIKey).where(APIKey.name == request.name)
            )
            if result.scalars().first():
                return JSONResponse(
                    status_code=400,
                    content={"message": "API name already exists"}
                )

            new_api = APIKey(
                name=request.name,
                provider=request.provider,
                token=request.token,
                max_tokens=request.max_tokens,
                model=request.model,
            )
            db.add(new_api)
            await db.commit()
            return {"status": "success"}
        except Exception as e:
            await db.rollback()
            return JSONResponse(
                status_code=500,
                content={"message": f"Database error: {str(e)}"}
            )


@api_router.post("/toggle-api/{api_name}")
async def toggle_api(api_name: str):
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(APIKey).where(APIKey.name == api_name))
            api = result.scalars().first()

            if not api:
                return JSONResponse(
                    status_code=404,
                    content={"message": "API with this name does not exist"}
                )

            if api.is_active:
                return JSONResponse(
                    status_code=200,
                    content={"message": "API is already active"}
                )

            await db.execute(update(APIKey).values(is_active=False))
            api.is_active = True
            await db.commit()

            return {"message": "API activated successfully. Other APIs were deactivated."}
        except Exception as e:
            await db.rollback()
            return JSONResponse(
                status_code=500,
                content={"message": f"Database error: {str(e)}"}
            )

@api_router.get("/get-apis")
async def get_apis():
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(APIKey))
            apis = result.scalars().all()
            return [
                {
                    "id": api.id,
                    "name": api.name,
                    "token": api.token,
                    "model": api.model,
                    "provider": api.provider,
                    "max_tokens": api.max_tokens,
                    "is_active": api.is_active,
                    "created_at": api.created_at.isoformat()
                }
                for api in apis
            ]
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Database error: {str(e)}"}
            )

@api_router.delete("/delete-api/{api_id}")
async def delete_api(api_id: int):
    async with SessionLocal() as db:
        try:
            stmt = delete(APIKey).where(APIKey.id == api_id)
            result = await db.execute(stmt)
            if result.rowcount > 0:
                await db.commit()
                return {"message": "API deleted successfully"}
            else:
                return JSONResponse(status_code=404, content={"message": "API not found"})
        except Exception as e:
            await db.rollback()
            return JSONResponse(
                status_code=500,
                content={"message": f"Database error: {str(e)}"}
            )

