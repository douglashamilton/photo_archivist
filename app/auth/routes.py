"""Authentication routes for Microsoft login and session management."""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.domain import User, AuthToken
from .msal_client import build_msal_app, get_token

router = APIRouter()


@router.get("/login")
async def login():
    """Initiate Microsoft login flow."""
    raise NotImplementedError()


@router.get("/callback")
async def auth_callback():
    """Handle OAuth callback and token acquisition."""
    raise NotImplementedError()


@router.post("/logout")
async def logout():
    """Clear session and perform logout."""
    raise NotImplementedError()


@router.get("/me")
async def get_current_user() -> Optional[User]:
    """Get the current authenticated user."""
    raise NotImplementedError()