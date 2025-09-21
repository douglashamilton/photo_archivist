"""Shortlist management API routes."""
from fastapi import APIRouter, Depends, HTTPException
from ..models.domain import Asset, Shortlist
from ..models.repo import Repository
from .builder import build_shortlist, update_shortlist_status


router = APIRouter()


@router.post("/build")
async def trigger_build(size: int = 20):
    """Trigger shortlist generation."""
    raise NotImplementedError()


@router.post("/{photo_id}/approve")
async def approve_photo(photo_id: str):
    """Add photo to shortlist."""
    raise NotImplementedError()


@router.post("/{photo_id}/remove")
async def remove_photo(photo_id: str):
    """Remove photo from shortlist."""
    raise NotImplementedError()


@router.get("/latest")
async def get_latest():
    """Get the latest shortlist."""
    raise NotImplementedError()