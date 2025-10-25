from __future__ import annotations

from datetime import datetime
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


class ScanRequest(BaseModel):
    month: Optional[str] = Field(
        default=None,
        description="Month bucket to scan in YYYY-MM format. Defaults to previous month.",
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Optional shortlist size override. Defaults to configured value.",
    )


class ScanResponse(BaseModel):
    run_id: int
    month: str
    total_items: int
    eligible_items: int
    shortlisted_items: int
    delta_cursor: str


class ShortlistItem(BaseModel):
    drive_item_id: str
    filename: Optional[str]
    captured_at: Optional[datetime]
    width: Optional[int]
    height: Optional[int]
    quality_score: Optional[float]
    download_url: Optional[str]
    rank: Optional[int]


class ShortlistResponse(BaseModel):
    month: str
    items: list[ShortlistItem]
