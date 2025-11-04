from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.models import ScanOutcome, ScanRequest, ScanState, ScanStatus
from app.services import ScanManager


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Photo Archivist")
scan_manager = ScanManager()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """Render the landing page with the scan request form."""
    context = _build_context(
        request,
        form_values={"directory": "", "start_date": "", "end_date": ""},
        errors=[],
        scan_attempted=False,
        status=None,
        outcome=None,
    )
    return templates.TemplateResponse(request, "index.html", context)


@app.post("/api/scans")
async def create_scan(
    request: Request,
    directory: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
) -> Response:
    """Create a scan job and return either HTML (HTMX) or JSON (API clients)."""
    payload = {
        "directory": directory,
        "start_date": start_date,
        "end_date": end_date,
    }
    form_values = {
        "directory": directory,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    try:
        scan_request = ScanRequest.model_validate(payload)
    except ValidationError as exc:
        errors = [error["msg"] for error in exc.errors()]
        context = _build_context(
            request,
            form_values=form_values,
            errors=errors,
            scan_attempted=True,
            status=None,
            outcome=None,
        )

        if _wants_json(request):
            return JSONResponse(
                {"errors": errors},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if request.headers.get("hx-request") == "true":
            return templates.TemplateResponse(
                request,
                "partials/shortlist.html",
                context,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return templates.TemplateResponse(request, "index.html", context, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    scan_id = scan_manager.enqueue(scan_request)
    status_snapshot, outcome_snapshot = scan_manager.snapshot(scan_id)

    context = _build_context(
        request,
        form_values=form_values,
        errors=[],
        scan_attempted=True,
        status=status_snapshot,
        outcome=outcome_snapshot,
    )

    if _wants_json(request):
        return JSONResponse(
            _serialize_status(status_snapshot, outcome_snapshot),
            status_code=status.HTTP_202_ACCEPTED,
        )

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            request,
            "partials/shortlist.html",
            context,
            status_code=status.HTTP_202_ACCEPTED,
        )

    return templates.TemplateResponse(request, "index.html", context, status_code=status.HTTP_202_ACCEPTED)


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: UUID) -> Response:
    """Return scan status and results as JSON."""
    status_snapshot, outcome_snapshot = scan_manager.snapshot(scan_id)
    if status_snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    return JSONResponse(_serialize_status(status_snapshot, outcome_snapshot))


@app.post("/api/scans/{scan_id}/photos/{photo_id}/selection")
async def update_photo_selection(
    request: Request,
    scan_id: UUID,
    photo_id: UUID,
    selected: bool = Form(...),
) -> Response:
    """Toggle selection state for a shortlisted photo."""
    status_snapshot, outcome_snapshot, updated = scan_manager.set_selection(scan_id, photo_id, selected)
    if status_snapshot is None or outcome_snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found in shortlist.")

    context = _build_context(
        request,
        form_values={"directory": "", "start_date": "", "end_date": ""},
        errors=[],
        scan_attempted=True,
        status=status_snapshot,
        outcome=outcome_snapshot,
    )

    if _wants_json(request):
        return JSONResponse(_serialize_status(status_snapshot, outcome_snapshot))

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(request, "partials/shortlist.html", context)

    return templates.TemplateResponse(request, "index.html", context)


@app.get("/fragments/shortlist/{scan_id}", response_class=HTMLResponse)
async def shortlist_fragment(request: Request, scan_id: UUID) -> HTMLResponse:
    """Serve the shortlist fragment for HTMX polling."""
    status_snapshot, outcome_snapshot = scan_manager.snapshot(scan_id)
    if status_snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    context = _build_context(
        request,
        form_values={"directory": "", "start_date": "", "end_date": ""},
        errors=[],
        scan_attempted=True,
        status=status_snapshot,
        outcome=outcome_snapshot,
    )
    return templates.TemplateResponse(request, "partials/shortlist.html", context)


@app.get("/api/thumbnails/{scan_id}/{photo_id}")
async def get_thumbnail(scan_id: UUID, photo_id: UUID) -> Response:
    """Stream a generated thumbnail image for a shortlisted photo."""
    outcome = scan_manager.get_outcome(scan_id)
    if outcome is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    photo = next((item for item in outcome.results if item.id == photo_id), None)
    if photo is None or photo.thumbnail_path is None or not photo.thumbnail_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not available.")

    return FileResponse(path=photo.thumbnail_path, media_type="image/jpeg")


def _build_context(
    request: Request,
    *,
    form_values: Dict[str, str],
    errors: list[str],
    scan_attempted: bool,
    status: Optional[ScanStatus],
    outcome: Optional[ScanOutcome],
) -> Dict[str, Any]:
    scan_state = status.state.value if status else ("idle" if not scan_attempted else "idle")
    scan_id = str(status.id) if status else None
    progress = {
        "processed": status.processed if status else 0,
        "total": status.total if status else 0,
        "matched": status.matched if status else 0,
    }

    results = []
    total_files = 0
    matched_files = 0

    if status and status.state == ScanState.COMPLETE and outcome:
        results = outcome.results
        total_files = outcome.total_files
        matched_files = outcome.matched_files
    elif outcome:
        results = outcome.results
        total_files = outcome.total_files
        matched_files = outcome.matched_files
    elif status:
        total_files = status.total
        matched_files = status.matched

    context: Dict[str, Any] = {
        "request": request,
        "page_title": "Photo Archivist",
        "results": results,
        "summary": {"total": total_files, "matched": matched_files},
        "errors": errors,
        "scan_attempted": scan_attempted,
        "form_values": form_values,
        "scan_state": scan_state,
        "scan_id": scan_id,
        "progress": progress,
        "status_message": status.message if status else None,
    }
    return context


def _serialize_status(status: Optional[ScanStatus], outcome: Optional[ScanOutcome]) -> Dict[str, Any]:
    if status is None:
        return {}

    results_payload: list[Dict[str, Any]] = []
    if outcome and status.state == ScanState.COMPLETE:
        results_payload = [
            {
                "id": str(photo.id),
                "filename": photo.filename,
                "captured_at": photo.captured_at.isoformat(),
                "brightness": photo.brightness,
                "used_fallback": photo.used_fallback,
                "path": str(photo.path),
                "thumbnail_url": f"/api/thumbnails/{status.id}/{photo.id}" if photo.thumbnail_path else None,
                "thumbnail_generated_at": photo.thumbnail_generated_at.isoformat()
                if photo.thumbnail_generated_at is not None
                else None,
                "selected": photo.selected,
            }
            for photo in outcome.results
        ]

    total_files = outcome.total_files if outcome else status.total
    matched_files = outcome.matched_files if outcome else status.matched

    return {
        "id": str(status.id),
        "state": status.state.value,
        "processed": status.processed,
        "total": status.total,
        "matched": status.matched,
        "summary": {"total_files": total_files, "matched_files": matched_files},
        "message": status.message,
        "results": results_payload,
        "requested_at": status.requested_at.isoformat(),
        "updated_at": status.updated_at.isoformat(),
    }


def _wants_json(request: Request) -> bool:
    if request.headers.get("hx-request") == "true":
        return False
    accept = request.headers.get("accept") or ""
    return "application/json" in accept.lower()
