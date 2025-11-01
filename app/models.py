from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


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
    path: Path
    filename: str
    captured_at: datetime
    brightness: float
    used_fallback: bool


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
