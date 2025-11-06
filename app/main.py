import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from uuid import UUID

from fastapi import FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.models import PrintOrderRequest, ScanOutcome, ScanRequest, ScanState, ScanStatus
from app.services import PrintOrderService, ScanManager
from app.services.print_orders import (
    NoSelectedPhotosError,
    PrintOrderConfigurationError,
    PrintOrderError,
    ProdigiAPIError,
    UnknownScanError,
)


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Photo Archivist")
scan_manager = ScanManager()
print_order_service = PrintOrderService(scan_manager)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _default_print_form_values() -> Dict[str, str]:
    return {
        "name": "",
        "email": "",
        "line1": "",
        "line2": "",
        "city": "",
        "state": "",
        "postal_code": "",
        "country_code": "",
        "shipping_method": "STANDARD",
        "copies": "1",
        "asset_base_url": os.getenv("PHOTO_ARCHIVIST_ASSET_BASE_URL", ""),
    }


def _capture_print_form_values(source: Mapping[str, Any]) -> Dict[str, str]:
    values = _default_print_form_values()
    for field in values.keys():
        raw_value = source.get(field)
        if raw_value is None:
            continue
        values[field] = str(raw_value)
    return values


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
                headers=_print_refresh_headers(None),
            )

        return templates.TemplateResponse(
            request,
            "index.html",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=_print_refresh_headers(None),
        )

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
            headers=_print_refresh_headers(scan_id),
        )

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            request,
            "partials/shortlist.html",
            context,
            status_code=status.HTTP_202_ACCEPTED,
            headers=_print_refresh_headers(scan_id),
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        context,
        status_code=status.HTTP_202_ACCEPTED,
        headers=_print_refresh_headers(scan_id),
    )


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
        return JSONResponse(
            _serialize_status(status_snapshot, outcome_snapshot),
            headers=_print_refresh_headers(status_snapshot.id if status_snapshot else None),
        )

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            request,
            "partials/shortlist.html",
            context,
            headers=_print_refresh_headers(status_snapshot.id if status_snapshot else None),
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        context,
        headers=_print_refresh_headers(status_snapshot.id if status_snapshot else None),
    )


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


@app.get("/fragments/print", response_class=HTMLResponse)
@app.get("/fragments/print/{scan_id}", response_class=HTMLResponse)
async def print_controls_fragment(
    request: Request,
    scan_id: Optional[UUID] = None,
    scan_id_query: Optional[UUID] = Query(default=None, alias="scan_id"),
) -> HTMLResponse:
    """Serve the print controls fragment, refreshing selection state as needed."""
    effective_scan_id = scan_id or scan_id_query
    status_snapshot: Optional[ScanStatus] = None
    outcome_snapshot: Optional[ScanOutcome] = None
    scan_attempted = False

    if effective_scan_id is not None:
        status_snapshot, outcome_snapshot = scan_manager.snapshot(effective_scan_id)
        if status_snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
        scan_attempted = True

    context = _build_context(
        request,
        form_values={"directory": "", "start_date": "", "end_date": ""},
        errors=[],
        scan_attempted=scan_attempted,
        status=status_snapshot,
        outcome=outcome_snapshot,
    )
    return templates.TemplateResponse(request, "partials/print_controls.html", context)


@app.post("/api/prints")
async def submit_print_order(request: Request) -> Response:
    """Submit a print order using either JSON (API clients) or form data (HTMX)."""
    content_type = request.headers.get("content-type", "").lower()
    is_json = "application/json" in content_type

    if is_json:
        payload = await request.json()
        header_scan_id: Optional[UUID] = None
        raw_scan_id = payload.get("scan_id")
        if raw_scan_id:
            try:
                header_scan_id = UUID(str(raw_scan_id))
            except (ValueError, TypeError):
                header_scan_id = None
        try:
            order_request = PrintOrderRequest.model_validate(payload)
        except ValidationError as exc:
            return JSONResponse(
                {"errors": exc.errors()},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                headers=_print_refresh_headers(header_scan_id),
            )

        try:
            submission = await print_order_service.submit_print_order(order_request)
        except UnknownScanError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except (PrintOrderConfigurationError, NoSelectedPhotosError) as exc:
            return JSONResponse(
                {"errors": [str(exc)]},
                status_code=status.HTTP_400_BAD_REQUEST,
                headers=_print_refresh_headers(order_request.scan_id),
            )
        except ProdigiAPIError as exc:
            return JSONResponse(
                {"errors": [str(exc)], "status": "error"},
                status_code=status.HTTP_502_BAD_GATEWAY,
                headers=_print_refresh_headers(order_request.scan_id),
            )
        except PrintOrderError as exc:
            return JSONResponse(
                {"errors": [str(exc)]},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                headers=_print_refresh_headers(order_request.scan_id),
            )

        return JSONResponse(
            {"orderId": submission.order_id, "status": submission.status},
            status_code=status.HTTP_202_ACCEPTED,
            headers=_print_refresh_headers(order_request.scan_id),
        )

    form = await request.form()
    form_values = _capture_print_form_values(form)

    scan_id_raw = form.get("scan_id")
    errors: list[str] = []
    scan_id: Optional[UUID] = None
    status_snapshot: Optional[ScanStatus] = None
    outcome_snapshot: Optional[ScanOutcome] = None
    scan_attempted = False

    if not scan_id_raw:
        errors.append("Scan identifier is required before submitting a print order.")
    else:
        try:
            scan_id = UUID(str(scan_id_raw))
        except (ValueError, TypeError):
            errors.append("Scan identifier is invalid.")

    if scan_id and not errors:
        status_snapshot, outcome_snapshot = scan_manager.snapshot(scan_id)
        if status_snapshot is None:
            errors.append("Scan not found or has expired. Please run the scan again.")
        else:
            scan_attempted = True

    selected_photo_ids: list[UUID] = []
    form_photo_ids: list[str] = []
    if hasattr(form, "getlist"):
        form_photo_ids = [value for value in form.getlist("photo_ids") if value]

    if form_photo_ids:
        try:
            selected_photo_ids = [UUID(str(value)) for value in form_photo_ids]
        except (ValueError, TypeError):
            errors.append("Invalid photo identifier submitted.")
            selected_photo_ids = []

    if not selected_photo_ids and scan_id and not errors:
        selected_photo_ids = [photo.id for photo in scan_manager.get_selected_results(scan_id)]

    request_payload = {
        "scan_id": scan_id,
        "photo_ids": selected_photo_ids,
        "recipient": {
            "name": form.get("name", ""),
            "email": form.get("email", ""),
            "address": {
                "line1": form.get("line1", ""),
                "line2": form.get("line2") or None,
                "city": form.get("city", ""),
                "state": form.get("state") or None,
                "postal_code": form.get("postal_code", ""),
                "country_code": form.get("country_code", ""),
            },
        },
        "shipping_method": form.get("shipping_method", "STANDARD"),
        "copies": form.get("copies", "1"),
        "asset_base_url": form.get("asset_base_url") or None,
        "api_key": form.get("api_key") or None,
    }

    order_request: Optional[PrintOrderRequest] = None
    if not errors:
        try:
            order_request = PrintOrderRequest.model_validate(request_payload)
        except ValidationError as exc:
            errors.extend(error["msg"] for error in exc.errors())

    if errors:
        feedback = {"status": "error", "errors": errors}
        context = _build_context(
            request,
            form_values={"directory": "", "start_date": "", "end_date": ""},
            errors=[],
            scan_attempted=scan_attempted,
            status=status_snapshot,
            outcome=outcome_snapshot,
            print_form_values=form_values,
            print_feedback=feedback,
        )
        return templates.TemplateResponse(
            request,
            "partials/print_controls.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
            headers=_print_refresh_headers(scan_id),
        )

    assert order_request is not None  # for type checkers

    try:
        submission = await print_order_service.submit_print_order(order_request)
    except UnknownScanError as exc:
        feedback = {"status": "error", "errors": [str(exc)]}
        context = _build_context(
            request,
            form_values={"directory": "", "start_date": "", "end_date": ""},
            errors=[],
            scan_attempted=False,
            status=None,
            outcome=None,
            print_form_values=form_values,
            print_feedback=feedback,
        )
        return templates.TemplateResponse(
            request,
            "partials/print_controls.html",
            context,
            status_code=status.HTTP_404_NOT_FOUND,
            headers=_print_refresh_headers(scan_id),
        )
    except (PrintOrderConfigurationError, NoSelectedPhotosError) as exc:
        feedback = {"status": "error", "errors": [str(exc)]}
        context = _build_context(
            request,
            form_values={"directory": "", "start_date": "", "end_date": ""},
            errors=[],
            scan_attempted=scan_attempted,
            status=status_snapshot,
            outcome=outcome_snapshot,
            print_form_values=form_values,
            print_feedback=feedback,
        )
        return templates.TemplateResponse(
            request,
            "partials/print_controls.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
            headers=_print_refresh_headers(scan_id),
        )
    except ProdigiAPIError as exc:
        feedback = {"status": "error", "errors": [str(exc)]}
        context = _build_context(
            request,
            form_values={"directory": "", "start_date": "", "end_date": ""},
            errors=[],
            scan_attempted=scan_attempted,
            status=status_snapshot,
            outcome=outcome_snapshot,
            print_form_values=form_values,
            print_feedback=feedback,
        )
        return templates.TemplateResponse(
            request,
            "partials/print_controls.html",
            context,
            status_code=status.HTTP_502_BAD_GATEWAY,
            headers=_print_refresh_headers(scan_id),
        )
    except PrintOrderError as exc:
        feedback = {"status": "error", "errors": [str(exc)]}
        context = _build_context(
            request,
            form_values={"directory": "", "start_date": "", "end_date": ""},
            errors=[],
            scan_attempted=scan_attempted,
            status=status_snapshot,
            outcome=outcome_snapshot,
            print_form_values=form_values,
            print_feedback=feedback,
        )
        return templates.TemplateResponse(
            request,
            "partials/print_controls.html",
            context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers=_print_refresh_headers(scan_id),
        )

    success_feedback = {
        "status": "success",
        "order_id": submission.order_id,
        "message": "Print order submitted successfully.",
    }
    # Refresh job snapshot in case state changed while submitting.
    if scan_id:
        status_snapshot, outcome_snapshot = scan_manager.snapshot(scan_id)
        scan_attempted = status_snapshot is not None

    context = _build_context(
        request,
        form_values={"directory": "", "start_date": "", "end_date": ""},
        errors=[],
        scan_attempted=scan_attempted,
        status=status_snapshot,
        outcome=outcome_snapshot,
        print_form_values=form_values,
        print_feedback=success_feedback,
    )
    return templates.TemplateResponse(
        request,
        "partials/print_controls.html",
        context,
        status_code=status.HTTP_202_ACCEPTED,
        headers=_print_refresh_headers(scan_id),
    )


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
    print_form_values: Optional[Dict[str, str]] = None,
    print_feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    scan_state = status.state.value if status else ("idle" if not scan_attempted else "idle")
    scan_id = str(status.id) if status else None
    progress = {
        "processed": status.processed if status else 0,
        "total": status.total if status else 0,
        "matched": status.matched if status else 0,
    }

    results: list[Any] = []
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

    selected_count = sum(1 for photo in results if getattr(photo, "selected", False))

    final_print_form_values = _default_print_form_values()
    if print_form_values:
        final_print_form_values.update(print_form_values)

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
        "print_form_values": final_print_form_values,
        "print_feedback": print_feedback,
        "selected_count": selected_count,
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
def _print_refresh_headers(scan_id: Optional[UUID]) -> Dict[str, str]:
    if scan_id is None:
        return {}
    return {"HX-Trigger": json.dumps({"print-refresh": {"scan_id": str(scan_id)}})}
