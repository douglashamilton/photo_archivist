from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool
    version: str
    service: str


class AuthConnectRequest(BaseModel):
    flow: str = Field(
        default="pkce",
        description="Authentication flow: pkce (default) or device_code.",
    )


class AuthConnectResponse(BaseModel):
    status: str
    flow: Optional[str] = None
    accounts: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
