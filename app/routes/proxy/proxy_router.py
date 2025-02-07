from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.future import select 
from sqlalchemy import delete
from app.models.database import SessionLocal
from app.models.database import ProxySettings
from app.proxy.embedded_mitm import EmbeddedMitm
from app.proxy.inspectors.flask_inspector import FlaskInspector
from app.proxy.inspectors.laravel_inspector import LaravelInspector
import asyncio
from pathlib import Path


proxy_router = APIRouter(prefix="/proxy", tags=["Proxy"])

# Global variables
mitm_inspector = None
log_memory = []

# Mapping frameworks to their respective inspector classes
INSPECTOR_CLASSES = {
    "Flask": FlaskInspector,
    "Laravel": LaravelInspector,
}

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
            "source_path": proxy.source_path,
            "burpsuite": proxy.burpsuite,
            "framework": proxy.framework
        }



@proxy_router.post("/save-proxy")
async def save_proxy(
    ip: str = Form(...),
    port: int = Form(...),
    proxy_type: str = Form(...),
    source_path: str = Form(...),
    burpsuite: str = Form(...),
    framework: str = Form(...)
):
    async with SessionLocal() as db:
        try:
            # Clear existing proxy
            await db.execute(delete(ProxySettings))

            new_proxy = ProxySettings(
                ip=ip,
                port=port,
                proxy_type="zerodayf_to_browser" if proxy_type == "1" else "zerodayf_to_burpsuite",
                source_path=source_path,
                burpsuite=burpsuite,
                framework=framework
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
        framework = proxy.framework

        inspector_class = INSPECTOR_CLASSES.get(framework)
        if not inspector_class:
            return JSONResponse(
                status_code=400,
                content={"message": f"No inspector available for framework '{framework}'"}
            )

        if proxy.proxy_type == "zerodayf_to_browser":
            # Normal proxy
            mitm_inspector = EmbeddedMitm(
                app_root=Path(proxy.source_path) if proxy.source_path else Path("/tmp"),
                log_memory=log_memory,
                listen_host=listen_host,
                listen_port=listen_port,
                inspector_class=inspector_class
            )

        elif proxy.proxy_type == "zerodayf_to_burpsuite":
            # Upstream to Burp
            if not proxy.burpsuite:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Burpsuite upstream URL not set"}
                )
            mitm_inspector = EmbeddedMitm(
                app_root=Path(proxy.source_path) if proxy.source_path else Path("/tmp"),
                log_memory=log_memory,
                listen_host=listen_host,
                listen_port=listen_port,
                mode=[f"upstream:{proxy.burpsuite}"],
                upstream_cert=False,
                inspector_class=inspector_class
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": "Invalid proxy type"}
            )

    await mitm_inspector.start()
    return {"message": "Proxy started successfully"}


@proxy_router.post("/stop")
async def stop_proxy():
    global mitm_inspector, log_memory

    if not mitm_inspector or not mitm_inspector.is_running:
        return JSONResponse(
            status_code=400,
            content={"message": "No proxy is running"}
        )

    await mitm_inspector.stop()

    # Clear the global log memory so the next run starts fresh
    log_memory.clear()

    return {"message": "Proxy stopped successfully"}


@proxy_router.get("/is-running")
def is_running():
    global mitm_inspector
    return {"is_running": bool(mitm_inspector and mitm_inspector.is_running)}


@proxy_router.get("/stream-logs")
async def stream_logs():
    global log_memory

    async def log_generator():
        idx = 0
        while True:
            if idx < len(log_memory):
                new_lines = log_memory[idx:]
                for line in new_lines:
                    # TODO: it might be a good idea to return raw JSON, but wouldn't that make it difficult to grab specific route logs?
                    yield f"data: {line}\n\n"
                idx = len(log_memory)
            else:
                await asyncio.sleep(0.5)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


# BUG: this make this app vulnerable to path traversal but then again, the app explicitly requires access to filesystem so it can't be prevented 
@proxy_router.get("/get-file")
def get_file(path: str):
    with open(path, "r") as f:
        return {"content": f.read()}

