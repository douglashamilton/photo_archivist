import logging

from fastapi import FastAPI

from .config import settings
from .schemas import HealthResponse

logger = logging.getLogger("photo_archivist")
logging.basicConfig(level=logging.INFO)


app = FastAPI(title="Photo Archivist")


@app.on_event("startup")
def on_startup():
    logger.info(
        {
            "event": "boot",
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "env": settings.ENV,
        }
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    logger.debug({"event": "health.check"})
    return HealthResponse(ok=True, version=settings.VERSION, service=settings.APP_NAME)
