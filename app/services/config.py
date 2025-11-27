from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class ScanConfig:
    allowed_extensions: tuple[str, ...] = field(default_factory=lambda: (".jpg", ".jpeg", ".jpe", ".jfif"))
    shortlist_limit: int = 5
    brightness_drop: float = 30.0
    brightness_soft: float = 50.0
    contrast_drop: float = 10.0
    blur_drop: float = 50.0
    blur_soft: float = 120.0
    min_dimension: int = 600
    min_aspect: float = 0.33
    max_aspect: float = 3.0
    distance_threshold: int = 5
    keep_per_cluster: int = 2
    aesthetic_model: str = "cafeai/cafe_aesthetic"
    aesthetic_backend: str = ""
    debug_report: bool = False
    debug_dir: str = "tmp"

    @classmethod
    def from_env(cls) -> "ScanConfig":
        return cls(
            allowed_extensions=tuple(
                ext.strip().lower()
                for ext in os.getenv("PHOTO_ARCHIVIST_EXTENSIONS", ".jpg,.jpeg,.jpe,.jfif").split(",")
                if ext.strip()
            ),
            shortlist_limit=int(os.getenv("PHOTO_ARCHIVIST_SHORTLIST_LIMIT", "5")),
            brightness_drop=float(os.getenv("PHOTO_ARCHIVIST_BRIGHTNESS_DROP", "30.0")),
            brightness_soft=float(os.getenv("PHOTO_ARCHIVIST_BRIGHTNESS_SOFT", "50.0")),
            contrast_drop=float(os.getenv("PHOTO_ARCHIVIST_CONTRAST_DROP", "10.0")),
            blur_drop=float(os.getenv("PHOTO_ARCHIVIST_BLUR_DROP", "50.0")),
            blur_soft=float(os.getenv("PHOTO_ARCHIVIST_BLUR_SOFT", "120.0")),
            min_dimension=int(os.getenv("PHOTO_ARCHIVIST_MIN_DIMENSION", "600")),
            min_aspect=float(os.getenv("PHOTO_ARCHIVIST_MIN_ASPECT", "0.33")),
            max_aspect=float(os.getenv("PHOTO_ARCHIVIST_MAX_ASPECT", "3.0")),
            distance_threshold=int(os.getenv("PHOTO_ARCHIVIST_DISTANCE_THRESHOLD", "5")),
            keep_per_cluster=int(os.getenv("PHOTO_ARCHIVIST_KEEP_PER_CLUSTER", "2")),
            aesthetic_model=os.getenv("PHOTO_ARCHIVIST_AESTHETIC_MODEL", "cafeai/cafe_aesthetic"),
            aesthetic_backend=os.getenv("PHOTO_ARCHIVIST_AESTHETIC_BACKEND", ""),
            debug_report=os.getenv("PHOTO_ARCHIVIST_DEBUG_REPORT", "false").lower() in {"1", "true", "yes", "on"},
            debug_dir=os.getenv("PHOTO_ARCHIVIST_DEBUG_DIR", "tmp"),
        )
