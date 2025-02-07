from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routes.api.api_router import api_router
from .routes.proxy.proxy_router import proxy_router
from .routes.scan.scan_router import scan_router, get_scan_result
from .routes.usage.usage_router import usage_router
from .models.database import create_tables, get_db, AsyncSession, CodeScans
from sqlalchemy.future import select 
import os

app = FastAPI()


# Define paths for templates and static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await create_tables()


# Custom Jinja function for static URLs
def static_url(request: Request, filename: str) -> str:
    return f"{request.base_url}static/{filename}"

templates.env.globals["static_url"] = static_url

#######################
# HTML Routes
#######################
@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/proxy-log")
async def proxy_log(request: Request):
    return templates.TemplateResponse("proxy_log.html", {"request": request})

@app.get("/route-log")
async def route_log(request: Request):
    return templates.TemplateResponse("route_log.html", {"request": request})

@app.get("/scans")
async def scans(request: Request):
    return templates.TemplateResponse("scans.html", {"request": request})

@app.get("/scan-templates")
async def scan_templates(request: Request):
    return templates.TemplateResponse("scan_templates.html", {"request": request})

@app.get("/manage-api")
async def manage_api(request: Request):
    return templates.TemplateResponse("manage_api.html", {"request": request})


@app.get("/usage")
async def usage(request: Request):
    return templates.TemplateResponse("usage.html", {"request": request})


@app.get("/scans/scan-result/{scan_name}")
async def scan_result_page(request: Request, scan_name: str):
    return templates.TemplateResponse(
        "scan_result.html",
        {
            "request": request,
            "scan_name": scan_name
        }
    )


# Register routers
app.include_router(api_router)
app.include_router(proxy_router)
app.include_router(scan_router)
app.include_router(usage_router)
