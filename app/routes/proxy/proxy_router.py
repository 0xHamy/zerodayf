from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.future import select 
from sqlalchemy import delete
from app.models.database import SessionLocal
from app.models.database import ProxySettings
from app.proxy.embedded_mitm import EmbeddedMitm
from app.proxy.inspectors.route_inspector import RouteInspector
import asyncio
from pathlib import Path


proxy_router = APIRouter(prefix="/proxy", tags=["Proxy"])

# Global variables
mitm_inspector = None
log_memory = []

@proxy_router.get("/get-proxy")
async def get_proxy():
    async with SessionLocal() as db:
        result = await db.execute(select(ProxySettings))
        proxy = result.scalars().first()
        if not proxy:
            return {}
        return {
            "ip": proxy.ip,
            "port": proxy.port,
            "proxy_type": proxy.proxy_type,
            "burpsuite": proxy.burpsuite
        }

@proxy_router.post("/save-proxy")
async def save_proxy(
    ip: str = Form(...),
    port: int = Form(...),
    proxy_type: str = Form(...),
    burpsuite: str = Form(...)
):
    async with SessionLocal() as db:
        try:
            # Clear existing proxy
            await db.execute(delete(ProxySettings))

            new_proxy = ProxySettings(
                ip=ip,
                port=port,
                proxy_type="zerodayf_to_browser" if proxy_type == "1" else "zerodayf_to_burpsuite",
                burpsuite=burpsuite
            )
            db.add(new_proxy)
            await db.commit()
            return {"status": "success", "message": "Proxy settings saved!"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@proxy_router.post("/start")
async def start_proxy():
    global mitm_inspector

    try:
        # Check if proxy is already running
        if mitm_inspector and mitm_inspector.is_running:
            return JSONResponse(
                status_code=400,
                content={"message": "Proxy is already running"}
            )

        async with SessionLocal() as db:
            result = await db.execute(select(ProxySettings))
            proxy = result.scalars().first()
            if not proxy:
                return JSONResponse(
                    status_code=404,
                    content={"message": "Proxy settings not found"}
                )

            listen_host = proxy.ip
            listen_port = proxy.port

            if proxy.proxy_type == "zerodayf_to_browser":
                mitm_inspector = EmbeddedMitm(
                    log_memory=log_memory,
                    listen_host=listen_host,
                    listen_port=listen_port
                )
            elif proxy.proxy_type == "zerodayf_to_burpsuite":
                if not proxy.burpsuite:
                    return JSONResponse(
                        status_code=400,
                        content={"message": "Burpsuite upstream URL not set"}
                    )
                mitm_inspector = EmbeddedMitm(
                    log_memory=log_memory,
                    listen_host=listen_host,
                    listen_port=listen_port,
                    mode=[f"upstream:{proxy.burpsuite}"],
                    upstream_cert=False
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Invalid proxy type"}
                )

        await mitm_inspector.start()
        return {"message": "Proxy started successfully"}

    except Exception as e:
        # Clean up if start failed
        if mitm_inspector:
            try:
                await mitm_inspector.stop()
            except:
                pass
            mitm_inspector = None
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to start proxy: {str(e)}"}
        )

@proxy_router.post("/stop")
async def stop_proxy():
    global mitm_inspector, log_memory

    try:
        if not mitm_inspector or not mitm_inspector.is_running:
            return JSONResponse(
                status_code=400,
                content={"message": "No proxy is running"}
            )

        await mitm_inspector.stop()
        log_memory.clear()
        mitm_inspector = None
        return {"message": "Proxy stopped successfully"}
        
    except Exception as e:
        # Force cleanup even if there was an error
        log_memory.clear()
        mitm_inspector = None
        return JSONResponse(
            status_code=500,
            content={"message": f"Error stopping proxy: {str(e)}"}
        )

@proxy_router.get("/is-running")
def is_running():
    global mitm_inspector
    return {"is_running": bool(mitm_inspector and mitm_inspector.is_running)}

@proxy_router.get("/stream-logs")
async def stream_logs():
    global log_memory

    async def log_generator():
        idx = 0
        try:
            while True:
                if idx < len(log_memory):
                    new_lines = log_memory[idx:]
                    for line in new_lines:
                        yield f"data: {line}\n\n"
                    idx = len(log_memory)
                else:
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            # Gracefully handle connection closure
            print("Log stream connection closed")
            return

    response = StreamingResponse(log_generator(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response


