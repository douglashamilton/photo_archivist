from datetime import date
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.models import ScanRequest
from app.services import run_scan


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Photo Archivist")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """Render the landing page with the scan request form."""
    context = {
        "request": request,
        "page_title": "Photo Archivist",
        "results": [],
        "summary": {"total": 0, "matched": 0},
        "errors": [],
        "scan_attempted": False,
        "form_values": {"directory": "", "start_date": "", "end_date": ""},
    }
    return templates.TemplateResponse(request, "index.html", context)


@app.post("/api/scans", response_class=HTMLResponse)
async def create_scan(
    request: Request,
    directory: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
) -> HTMLResponse:
    """Process a scan request synchronously and return the shortlist partial."""
    payload = {
        "directory": directory,
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        scan_request = ScanRequest.model_validate(payload)
    except ValidationError as exc:
        context = {
            "request": request,
            "page_title": "Photo Archivist",
            "results": [],
            "summary": {"total": 0, "matched": 0},
            "errors": [error["msg"] for error in exc.errors()],
            "scan_attempted": True,
            "form_values": {
                "directory": directory,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }
        if request.headers.get("hx-request") == "true":
            return templates.TemplateResponse(request, "partials/shortlist.html", context)

        return templates.TemplateResponse(request, "index.html", context, status_code=200)

    outcome = run_scan(scan_request)
    context = {
        "request": request,
        "page_title": "Photo Archivist",
        "results": outcome.results,
        "summary": {
            "total": outcome.total_files,
            "matched": outcome.matched_files,
        },
        "errors": [],
        "scan_attempted": True,
        "form_values": {
            "directory": directory,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    }
    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(request, "partials/shortlist.html", context)

    return templates.TemplateResponse(request, "index.html", context)
