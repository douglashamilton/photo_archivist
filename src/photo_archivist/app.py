import logging

from fastapi import FastAPI

from .config import settings
from .schemas import HealthResponse
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

    # Initialize storage (creates SQLite file/tables if needed). Log only non-sensitive info.
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
