"""API schemas for request/response models."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

# Sync API schemas
class SyncRunRequest(BaseModel):
    """Request model for manual sync trigger."""
    mode: str = Field(default="manual", pattern="^manual$")


class SyncRunResponse(BaseModel):
    """Response model for sync run status."""
    started_at: datetime
    delta_link_set: bool


# Shortlist API schemas
class ShortlistItemResponse(BaseModel):
    """Response model for shortlist items."""
    item_id: str
    thumb_url: str
    final_score: float
    reasons: List[str]


class ShortlistResponse(BaseModel):
    """Response model for shortlist details."""
    id: UUID
    size: int
    items: List[ShortlistItemResponse]


class ShortlistSelectionRequest(BaseModel):
    """Request model for shortlist item selection."""
    item_id: str
    selected: bool


class ShortlistSelectionResponse(BaseModel):
    """Response model for shortlist item selection."""
    ok: bool


# Print API schemas
class PrintOrderRequest(BaseModel):
    """Request model for creating a print order."""
    shortlist_id: UUID
    sku: str = Field(default="photo_4x6", pattern="^photo_4x6$")


class PrintOrderResponse(BaseModel):
    """Response model for print order status."""
    provider: str
    mode: str
    order_id: str
    status: str


# Error responses
class ErrorResponse(BaseModel):
    """Generic error response model."""
    error: str
    detail: Optional[str] = None