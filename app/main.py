"""FastAPI application factory and route registration."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from .auth.routes import router as auth_router
from .shortlist.routes import router as shortlist_router
from .print.routes import router as print_router
from .ui.pages import router as pages_router
from .config import settings
from .models.domain import *  # noqa: F403
from .telemetry.log import setup_logging


# Global state
engine: AsyncEngine | None = None
templates: Jinja2Templates | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global engine, templates

    # Setup
    setup_logging()
    await init_database()
    setup_templates()

    yield

    # Cleanup
    if engine:
        await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Intelligent photo archival and printing system",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware for development
    if settings.debug:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Static files
    app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")

    # Register routers
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(shortlist_router, prefix="/shortlist", tags=["shortlist"])
    app.include_router(print_router, prefix="/print", tags=["print"])
    app.include_router(pages_router, tags=["pages"])

    return app


async def init_database() -> None:
    """Initialize database and create tables."""
    global engine

    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def setup_templates() -> None:
    """Initialize Jinja2 templates."""
    global templates
    templates = Jinja2Templates(directory="app/ui/templates")


# Create the FastAPI application instance
app = create_app()