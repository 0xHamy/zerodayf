from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routes.api.api_router import api_router
from .routes.endpoint_map.endpoint_map import endpoint_map_router
from .routes.code_analysis.analysis_template_router import template_analysis_router
from .routes.usage.usage_router import usage_router
from .routes.utils.utils_router import util_router
from .routes.code_analysis.analysis_router import analysis_router
from .models.database import create_tables, get_db, AsyncSession, CodeScans
from sqlalchemy.future import select 
import os, json, bleach
from markdown import markdown

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

@app.get("/endpoint-mapping")
async def endpoint_map(request: Request):
    return templates.TemplateResponse("endpoint_map.html", {"request": request})

@app.get("/code-map")
async def code_map(request: Request):
    return templates.TemplateResponse("code_map.html", {"request": request})

@app.get("/code-analysis")
async def code_analysis(request: Request):
    return templates.TemplateResponse("code_analysis.html", {"request": request})

@app.get("/analysis-templates")
async def analysis_templates(request: Request):
    return templates.TemplateResponse("analysis_templates.html", {"request": request})


@app.get("/manage-api")
async def manage_api(request: Request):
    return templates.TemplateResponse("manage_api.html", {"request": request})


@app.get("/usage")
async def usage(request: Request):
    return templates.TemplateResponse("usage.html", {"request": request})

import logging
logging.basicConfig(level=logging.DEBUG)

@app.get("/analysis/report/{scan_uid}")
async def analysis_report(scan_uid: str, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        query = select(CodeScans).where(CodeScans.uid == scan_uid)
        result = await db.execute(query)
        scan = result.scalar_one_or_none()

        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        formatted_date = scan.date.strftime("%m/%d/%Y, %I:%M:%S %p")
        formatted_result = None

        if scan.scan_type == "ai":
            # Convert Markdown to HTML
            html_content = markdown(scan.scan_result)
            # Define allowed tags and attributes
            allowed_tags = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'ul', 'ol', 'li',
                'table', 'thead', 'tbody', 'tr', 'th', 'td', 'code', 'pre', 'blockquote'
            ]
            allowed_attributes = {
                'a': ['href', 'title'],
                'img': ['src', 'alt', 'title'],
                'table': ['border', 'class'],
                'td': ['class'],
                'th': ['class']
            }
            # Sanitize the HTML
            formatted_result = bleach.clean(
                html_content,
                tags=allowed_tags,
                attributes=allowed_attributes,
                strip=True  # Remove disallowed tags instead of escaping them
            )
        elif scan.scan_type == "semgrep":
            # [Existing Semgrep logic remains unchanged]
            try:
                logging.debug(f"Raw scan_result: {scan.scan_result}")
                cleaned_json = scan.scan_result.replace('\n', '\\n').replace('\t', '\\t')
                scan_result_json = json.loads(cleaned_json)
                logging.debug(f"Parsed scan_result_json: {scan_result_json}")
                
                if "results" in scan_result_json:
                    findings = scan_result_json["results"]
                    grouped_findings = {}
                    for finding in findings:
                        path = finding["path"]
                        if path not in grouped_findings:
                            grouped_findings[path] = {
                                "path": path,
                                "scanned_code": finding.get("code", ""),
                                "results": []
                            }
                        grouped_findings[path]["results"].append(finding)
                    formatted_result = list(grouped_findings.values())
                    logging.debug(f"Formatted result: {formatted_result}")
                else:
                    formatted_result = []
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"JSON error: {str(e)}")
                formatted_result = {"error": f"Invalid Semgrep JSON: {str(e)}"}

        return templates.TemplateResponse(
            "view_report.html",
            {
                "request": request,
                "scan_name": scan.scan_name,
                "scan_uid": scan.uid,
                "scan_type": scan.scan_type,
                "scan_date": formatted_date,
                "scan_template": scan.scan_template,
                "scan_result": formatted_result
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Register routers
app.include_router(api_router)
app.include_router(template_analysis_router)
app.include_router(endpoint_map_router)
app.include_router(usage_router)
app.include_router(util_router)
app.include_router(analysis_router)

