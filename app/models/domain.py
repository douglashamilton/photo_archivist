"""Domain models and database schemas for the Photo Archivist application."""
from datetime import datetime
from enum import Enum
import json
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, JSON
from sqlalchemy.types import TypeDecorator, VARCHAR
from pydantic import field_validator, model_validator
from pydantic.config import ConfigDict


class ShortlistItemList(TypeDecorator):
    """Custom type for storing lists of ShortlistItems as JSON."""

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            # Convert list of ShortlistItem objects to list of dicts
            if isinstance(value, list):
                value = [
                    {
                        "asset_item_id": item.asset_item_id,
                        "rank": item.rank,
                        "selected": item.selected
                    } if isinstance(item, ShortlistItem) else item
                    for item in value
                ]
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
            # Convert list of dicts back to list of ShortlistItem objects
            if isinstance(value, list):
                value = [ShortlistItem(**item) if isinstance(item, dict) else item for item in value]
        return value


class PrintMode(str, Enum):
    """Print mode enumeration."""
    TEST = "test"
    LIVE = "live"


class PrintProvider(str, Enum):
    """Print provider enumeration."""
    KITE = "kite"


class PrintSku(str, Enum):
    """Print SKU enumeration."""
    PHOTO_4X6 = "photo_4x6"


class PrintOrderStatus(str, Enum):
    """Print order status enumeration."""
    QUEUED = "queued"
    SUBMITTED = "submitted"
    FAILED = "failed"


class ShortlistStatus(str, Enum):
    """Shortlist status enumeration."""
    DRAFT = "draft"
    FINALIZED = "finalized"


class User(SQLModel, table=True):
    """User entity with Microsoft Account details."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: str = Field(index=True)
    display_name: Optional[str] = None
    scopes: List[str] = Field(sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuthToken(SQLModel, table=True):
    """Authentication token storage."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    access_token: str  # Will be encrypted at rest
    refresh_token: str  # Will be encrypted at rest
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SyncState(SQLModel, table=True):
    """OneDrive delta sync state."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    delta_link: str
    last_run_at: datetime
    last_status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Asset(SQLModel, table=True):
    """Photo asset metadata."""
    
    item_id: str = Field(primary_key=True)  # OneDrive item ID
    user_id: UUID = Field(foreign_key="user.id", index=True)
    path: str
    taken_at: Optional[datetime] = Field(default=None, index=True)
    width: Optional[int] = None
    height: Optional[int] = None
    mime: Optional[str] = Field(default=None, index=True)
    mime_type: Optional[str] = Field(default=None)  # For backwards compatibility
    phash: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __hash__(self) -> int:
        """Make Asset hashable by item_id."""
        return hash(self.item_id)
        
    def __eq__(self, other: object) -> bool:
        """Compare assets by item_id."""
        if not isinstance(other, Asset):
            return NotImplemented
        return self.item_id == other.item_id

    def model_json(self) -> dict:
        """Convert model to JSON compatible dict."""
        return {
            "item_id": self.item_id,
            "user_id": str(self.user_id),
            "path": self.path,
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
            "width": self.width,
            "height": self.height,
            "mime": self.mime,
            "phash": self.phash,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class Score(SQLModel, table=True):
    """Photo quality scores."""
    
    asset_item_id: str = Field(foreign_key="asset.item_id", primary_key=True)
    sharpness: float = Field(ge=0.0, le=1.0)
    exposure: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0, index=True)
    rationale: List[str] = Field(sa_type=JSON)
    scored_at: datetime = Field(default_factory=datetime.utcnow)


class ShortlistItem(SQLModel):
    """Individual item in a shortlist."""
    
    asset_item_id: str = Field(foreign_key="asset.item_id")
    rank: int = Field(ge=0)
    selected: bool = Field(default=True)

    def dict(self, *args, **kwargs) -> dict:
        """Convert to a dictionary for JSON serialization."""
        return {
            "asset_item_id": self.asset_item_id,
            "rank": self.rank,
            "selected": self.selected
        }


class Shortlist(SQLModel, table=True):
    """Curated shortlist of photos."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    size: int = Field(ge=1)
    items: List[ShortlistItem] = Field(sa_type=ShortlistItemList, default=[])
    status: ShortlistStatus = Field(default=ShortlistStatus.DRAFT)


class PrintOrderItemList(TypeDecorator):
    """Custom type for storing lists of PrintOrderItems as JSON."""

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            # Convert list of PrintOrderItem objects to list of dicts
            if isinstance(value, list):
                value = [
                    {
                        "asset_item_id": item.asset_item_id,
                        "qty": item.qty
                    } if isinstance(item, PrintOrderItem) else item
                    for item in value
                ]
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
            # Convert list of dicts back to list of PrintOrderItem objects
            if isinstance(value, list):
                value = [PrintOrderItem(**item) if isinstance(item, dict) else item for item in value]
        return value


class PrintOrderItem(SQLModel):
    """Individual item in a print order."""
    
    asset_item_id: str = Field(foreign_key="asset.item_id")
    qty: int = Field(ge=1)

    def dict(self, *args, **kwargs) -> dict:
        """Convert to a dictionary for JSON serialization."""
        return {
            "asset_item_id": self.asset_item_id,
            "qty": self.qty
        }


class PrintOrder(SQLModel, table=True):
    """Print order details."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shortlist_id: UUID = Field(foreign_key="shortlist.id", index=True)
    provider: PrintProvider = Field(default=PrintProvider.KITE)
    mode: PrintMode = Field(
        default=PrintMode.TEST
    )
    sku: PrintSku = Field(default=PrintSku.PHOTO_4X6)
    items: List[PrintOrderItem] = Field(sa_type=PrintOrderItemList)

    items: List[PrintOrderItem] = Field(
        default_factory=list,
        sa_type=PrintOrderItemList,
        description="List of items to print, must not be empty"
    )
    mode: PrintMode = Field(
        default=PrintMode.TEST,
        description="Print mode (test/live). Live mode requires production API key"
    )

    def __init__(self, **data):
        """Initialize and validate print order."""
        super().__init__(**data)
        self._validate()

    def _validate(self):
        """Validate print order on creation and update."""
        if not self.items or len(self.items) == 0:
            raise ValueError("No photos selected for printing")
        if self.mode == PrintMode.LIVE:
            raise ValueError("Only test mode orders are supported")
    provider_order_id: Optional[str] = None
    status: PrintOrderStatus = Field(default=PrintOrderStatus.QUEUED)
    created_at: datetime = Field(default_factory=datetime.utcnow)