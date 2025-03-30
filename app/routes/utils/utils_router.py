from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select, func
from app.models.database import CodeScans
from app.models.database import SessionLocal
import asyncio, markdown, json, textwrap
from markdown import markdown as md_to_html


util_router = APIRouter(prefix="/utils", tags=["Utilities"])


@util_router.get("/download-report/ai/{uid}")
async def download_ai_report(
    uid: str,
    report_type: str = Query("pdf", description="Report format: 'pdf', 'html', or 'markdown'"),
    scan_type: str = Query(None, description="Optional scan type to validate against stored value")
):
    """
    Full route to download AI scan report: /utils/download-report/ai/ai_001?report_type=pdf
    """
    async with SessionLocal() as db:
        try:
            # Fetch the scan by UID
            result = await db.execute(
                select(CodeScans).where(func.lower(CodeScans.uid) == func.lower(uid))
            )
            scan = result.scalars().first()

            # Check if scan exists
            if not scan:
                return JSONResponse(
                    status_code=404,
                    content={"message": "Scan not found"}
                )

            # Check if scan_result is empty
            if not scan.scan_result:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Scan result is empty"}
                )

            # Optional: Validate scan_type if provided
            if scan_type and scan_type.lower() != scan.scan_type.lower():
                return JSONResponse(
                    status_code=400,
                    content={"message": "Scan type mismatch"}
                )

            # Handle PDF report type
            if report_type.lower() == "pdf":
                proc = await asyncio.create_subprocess_exec(
                    'pandoc',
                    '-f', 'markdown',
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
                    headers={"Content-Disposition": f'attachment; filename="{uid}.pdf"'}
                )

            # Handle HTML report type
            elif report_type.lower() == "html":
                html_content = f"""
                <html>
                <head><title>Scan Report</title></head>
                <body>
                {markdown.markdown(scan.scan_result)}
                </body>
                </html>
                """
                return Response(
                    content=html_content,
                    media_type="text/html",
                    headers={"Content-Disposition": f'attachment; filename="{uid}.html"'}
                )

            # Handle Markdown report type
            elif report_type.lower() == "markdown":
                return Response(
                    content=scan.scan_result,
                    media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="{uid}.md"'}
                )

            # Handle invalid report type
            else:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Invalid report type. Choose 'pdf', 'html', or 'markdown'"}
                )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Internal server error: {str(e)}"}
            )


def wrap_code(code, max_width=100):
    """
    Wrap code lines only if they exceed max_width, preserving indentation.
    """
    lines = code.splitlines()
    wrapped_lines = []
    
    for line in lines:
        # Calculate leading whitespace (indentation)
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent
        
        # Only wrap if the line exceeds max_width
        if len(line) > max_width:
            wrapper = textwrap.TextWrapper(
                width=max_width,
                break_long_words=True,
                replace_whitespace=False,
                initial_indent=indent_str,
                subsequent_indent=indent_str
            )
            wrapped_lines.extend(wrapper.wrap(line))
        else:
            wrapped_lines.append(line)
    
    return "\n".join(wrapped_lines)


def generate_markdown(scan_result):
    """
    Convert Semgrep JSON scan results to a Markdown string with sensible wrapping.
    """
    md = "# Semgrep Scan Report\n\n"
    wrapper = textwrap.TextWrapper(width=80, break_long_words=True, replace_whitespace=False)
    
    for result in scan_result.get("results", []):
        md += f"## Path: {result['path']}\n\n"
        # Wrap path only if excessively long
        wrapped_path = "\n".join(wrapper.wrap(f"Path: {result['path']}"))
        md = md.replace(f"## Path: {result['path']}", f"## {wrapped_path}")
        
        # Infer language for code block syntax highlighting
        lang = ""
        if result['path'].endswith(".html"):
            lang = "html"
        elif result['path'].endswith(".py"):
            lang = "python"
        
        # Wrap code while preserving structure
        wrapped_code = wrap_code(result['code'], max_width=100)
        md += f"**Code:**\n```{lang}\n{wrapped_code}\n```\n\n"
        
        md += f"**Severity:** {result['severity']}\n"
        md += f"**Impact:** {result['impact']}\n"
        md += f"**Message:** {result['message']}\n"
        md += f"**CWE:** {', '.join(result['cwe'])}\n\n"
        md += "---\n\n"
    return md


@util_router.get("/download-report/semgrep/{uid}")
async def download_semgrep_report(
    uid: str,
    report_type: str = Query("pdf", description="Report format: 'pdf', 'html', or 'markdown'"),
    scan_type: str = Query(None, description="Optional scan type to validate against stored value")
):
    """
    Download a Semgrep scan report in the specified format.
    Example: /utils/download-report/semgrep/semgrep_001?report_type=pdf
    """
    async with SessionLocal() as db:
        try:
            # Fetch the scan by UID
            result = await db.execute(
                select(CodeScans).where(func.lower(CodeScans.uid) == func.lower(uid))
            )
            scan = result.scalars().first()

            # Check if scan exists
            if not scan:
                return JSONResponse(status_code=404, content={"message": "Scan not found"})

            # Verify scan type is 'semgrep'
            if scan.scan_type.lower() != "semgrep":
                return JSONResponse(status_code=400, content={"message": "Invalid scan type for this route"})

            # Check if scan_result is empty
            if not scan.scan_result:
                return JSONResponse(status_code=400, content={"message": "Scan result is empty"})

            # Parse the JSON scan_result
            try:
                scan_result = json.loads(scan.scan_result)
            except json.JSONDecodeError:
                return JSONResponse(status_code=400, content={"message": "Invalid scan result format"})

            # Generate Markdown content from JSON
            md_content = generate_markdown(scan_result)

            # Handle Markdown report type
            if report_type.lower() == "markdown":
                return Response(
                    content=md_content,
                    media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="{uid}.md"'}
                )

            # Handle HTML report type
            elif report_type.lower() == "html":
                html_content = f"""
                <html>
                <head>
                    <title>Semgrep Scan Report</title>
                    <style>
                        pre {{ background: #f8f8f8; padding: 10px; border: 1px solid #e0e0e0; white-space: pre-wrap; }}
                        code {{ font-family: monospace; }}
                        body {{ font-family: Arial, sans-serif; }}
                    </style>
                </head>
                <body>
                {md_to_html(md_content, extensions=['fenced_code'])}
                </body>
                </html>
                """
                return Response(
                    content=html_content,
                    media_type="text/html",
                    headers={"Content-Disposition": f'attachment; filename="{uid}.html"'}
                )

            # Handle PDF report type
            elif report_type.lower() == "pdf":
                proc = await asyncio.create_subprocess_exec(
                    'pandoc',
                    '-f', 'markdown',
                    '-t', 'pdf',
                    '--wrap=auto',
                    '-V', 'fontsize=10pt',
                    '-V', 'geometry:margin=1in',
                    '-o', '-',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate(input=md_content.encode())
                if proc.returncode != 0:
                    error_msg = stderr.decode()
                    return JSONResponse(status_code=500, content={"message": f"PDF conversion failed: {error_msg}"})
                if not stdout:
                    return JSONResponse(status_code=500, content={"message": "Generated PDF is empty"})
                return Response(
                    content=stdout,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{uid}.pdf"'}
                )

            # Handle invalid report type
            else:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Invalid report type. Choose 'pdf', 'html', or 'markdown'"}
                )

        except Exception as e:
            return JSONResponse(status_code=500, content={"message": f"Internal server error: {str(e)}"})