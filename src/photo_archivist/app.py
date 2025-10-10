import logging
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .auth import get_msal_client
from .config import settings
from .schemas import (
    AuthConnectRequest,
    AuthConnectResponse,
    HealthResponse,
)
from .storage import get_engine, init_db

logger = logging.getLogger("photo_archivist")
logging.basicConfig(level=logging.INFO)


app = FastAPI(title="Photo Archivist")


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
