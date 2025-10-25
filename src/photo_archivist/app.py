import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .auth import get_msal_client
from .config import settings
from .schemas import (
    AuthConnectRequest,
    AuthConnectResponse,
    HealthResponse,
    ScanRequest,
    ScanResponse,
    ShortlistItem as ShortlistItemSchema,
    ShortlistResponse,
)
from .services import ScanService
from .storage import get_engine, get_session, init_db
from .graph import GraphClient

logger = logging.getLogger("photo_archivist")
logging.basicConfig(level=logging.INFO)


app = FastAPI(title="Photo Archivist")

_graph_client: Optional[GraphClient] = None
_scan_service: Optional[ScanService] = None


@app.on_event("startup")
def on_startup() -> None:
    logger.info(
        {
            "event": "boot",
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "env": settings.ENV,
        }
    )

    # Initialize storage (creates SQLite file/tables as needed).
    # Log only non-sensitive info.
    try:
        db_path = getattr(settings, "DB_PATH", None)
        engine = get_engine(db_path)
        init_db(engine)
        db_display = None
        if db_path is not None:
            # Only show the filename portion to avoid leaking absolute paths
            try:
                db_display = db_path.name if hasattr(db_path, "name") else str(db_path)
            except Exception:
                db_display = "<db>"

        logger.info({"event": "storage.initialized", "db": db_display})
    except Exception:
        logger.exception("storage.init failed")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    logger.debug({"event": "health.check"})
    return HealthResponse(ok=True, version=settings.VERSION, service=settings.APP_NAME)


@app.post("/api/auth/connect", response_model=AuthConnectResponse)
def auth_connect(request: AuthConnectRequest) -> AuthConnectResponse | JSONResponse:
    client = get_msal_client()
    flow = request.flow or "pkce"
    try:
        result: Dict[str, Any] = client.ensure_connected(flow=flow)
    except ValueError as exc:
        if str(exc) == "unsupported_flow":
            return JSONResponse(status_code=400, content={"error": "unsupported_flow"})
        raise
    return AuthConnectResponse(**result)


def _get_scan_service() -> ScanService:
    global _graph_client, _scan_service
    if _scan_service is None:

        def _token_supplier() -> str:
            msal_client = get_msal_client()
            return msal_client.get_token()

        _graph_client = GraphClient(
            token_supplier=_token_supplier,
            root_path=settings.GRAPH_ROOT_PATH,
            page_size=settings.GRAPH_PAGE_SIZE,
        )
        _scan_service = ScanService(
            graph_client=_graph_client,
            shortlist_size=settings.SCAN_SHORTLIST_SIZE,
            session_factory=get_session,
        )
    return _scan_service


@app.post("/api/run/scan", response_model=ScanResponse)
def trigger_scan(request: ScanRequest) -> ScanResponse:
    service = _get_scan_service()
    try:
        summary = service.run(month=request.month, limit=request.limit)
    except ValueError as exc:
        detail = str(exc)
        if detail in {"invalid_month", "invalid_shortlist_limit"}:
            raise HTTPException(status_code=400, detail=detail)
        raise
    except RuntimeError as exc:
        detail = str(exc)
        if detail in {"auth.not_connected", "auth.token_unavailable"}:
            raise HTTPException(status_code=409, detail=detail)
        raise

    return ScanResponse(
        run_id=summary.run_id,
        month=summary.month,
        total_items=summary.total_items,
        eligible_items=summary.eligible_items,
        shortlisted_items=summary.shortlisted_items,
        delta_cursor=summary.delta_cursor,
    )


@app.get("/api/shortlist", response_model=ShortlistResponse)
def get_shortlist(month: str = Query(default=..., description="Month in YYYY-MM format")) -> ShortlistResponse:
    service = _get_scan_service()
    try:
        items = service.shortlist_for_month(month)
    except ValueError as exc:
        if str(exc) == "invalid_month":
            raise HTTPException(status_code=400, detail="invalid_month")
        raise

    if not items:
        raise HTTPException(status_code=404, detail="shortlist_not_found")

    payload = [
        ShortlistItemSchema(
            drive_item_id=item.drive_item_id,
            filename=item.filename,
            captured_at=item.captured_at,
            width=item.width,
            height=item.height,
            quality_score=item.quality_score,
            download_url=item.download_url,
            rank=item.rank,
        )
        for item in items
    ]
    return ShortlistResponse(month=month, items=payload)
