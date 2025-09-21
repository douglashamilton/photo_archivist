"""Web UI page routes and handlers."""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from ..models.domain import Asset, Shortlist
from ..models.repo import Repository
from ..deps import get_repository


router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    repo: Repository = Depends(get_repository)
):
    """Render home page."""
    raise NotImplementedError()


@router.get("/shortlist", response_class=HTMLResponse)
async def shortlist_review(
    request: Request,
    repo: Repository = Depends(get_repository)
):
    """Render shortlist review page."""
    raise NotImplementedError()


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    repo: Repository = Depends(get_repository)
):
    """Render settings page."""
    raise NotImplementedError()


@router.get("/_partials/photo-grid", response_class=HTMLResponse)
async def photo_grid_partial(
    request: Request,
    repo: Repository = Depends(get_repository)
):
    """Render photo grid partial for HTMX updates."""
    raise NotImplementedError()


@router.get("/_partials/status", response_class=HTMLResponse)
async def sync_status_partial(
    request: Request,
    repo: Repository = Depends(get_repository)
):
    """Render sync status partial for HTMX updates."""
    raise NotImplementedError()