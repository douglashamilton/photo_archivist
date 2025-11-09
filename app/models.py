from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ScanRequest(BaseModel):
    directory: Path = Field(..., description="Absolute path to the photo library root.")
    start_date: date
    end_date: date

    @field_validator("directory")
    @classmethod
    def directory_must_exist(cls, value: Path) -> Path:
        if not value.exists():
            raise ValueError("Directory does not exist.")
        if not value.is_dir():
            raise ValueError("Path must be a directory.")
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> "ScanRequest":
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after the start date.")
        return self


@dataclass(slots=True)
class PhotoResult:
    id: UUID
    path: Path
    filename: str
    captured_at: datetime
    brightness: float
    used_fallback: bool
    thumbnail_path: Path | None = None
    thumbnail_generated_at: datetime | None = None
    selected: bool = False

    @classmethod
    def create(
        cls,
        *,
        path: Path,
        filename: str,
        captured_at: datetime,
        brightness: float,
        used_fallback: bool,
    ) -> "PhotoResult":
        return cls(
            id=uuid4(),
            path=path,
            filename=filename,
            captured_at=captured_at,
            brightness=brightness,
            used_fallback=used_fallback,
        )


@dataclass(slots=True)
class ScanOutcome:
    results: list[PhotoResult]
    total_files: int
    matched_files: int


class ScanState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass(slots=True)
class ScanStatus:
    id: UUID
    state: ScanState
    processed: int = 0
    total: int = 0
    matched: int = 0
    message: str | None = None
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PrintAddress(BaseModel):
    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code")

    @field_validator("line1", "city", "postal_code")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be blank.")
        return value

    @field_validator("state")
    @classmethod
    def _normalize_state(cls, value: str | None) -> str | None:
        if value is None:
            return None
        result = value.strip()
        return result or None

    @field_validator("country_code")
    @classmethod
    def _uppercase_country(cls, value: str) -> str:
        code = value.strip().upper()
        if len(code) != 2 or not code.isalpha():
            raise ValueError("Country code must be a two-letter ISO code.")
        return code


class PrintRecipient(BaseModel):
    name: str
    email: EmailStr
    address: PrintAddress

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Recipient name is required.")
        return value


class PrintOrderRequest(BaseModel):
    scan_id: UUID
    photo_ids: list[UUID]
    recipient: PrintRecipient
    shipping_method: str = Field(default="STANDARD")
    copies: int = Field(default=1, ge=1, le=10)
    asset_base_url: str | None = Field(default=None, description="HTTPS base URL for published assets")
    api_key: str | None = Field(default=None, description="Prodigi API key")

    @field_validator("photo_ids")
    @classmethod
    def _require_photo_ids(cls, value: list[UUID]) -> list[UUID]:
        if not value:
            raise ValueError("At least one photo must be selected for printing.")
        return value

    @field_validator("shipping_method")
    @classmethod
    def _shipping_not_blank(cls, value: str) -> str:
        method = value.strip().upper()
        if not method:
            raise ValueError("Shipping method is required.")
        return method

    @field_validator("asset_base_url", mode="before")
    @classmethod
    def _normalize_asset_base(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("api_key", mode="before")
    @classmethod
    def _normalize_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


@dataclass(slots=True)
class PrintOrderSubmission:
    order_id: str
    status: str
    raw_response: dict[str, Any] | None = None
