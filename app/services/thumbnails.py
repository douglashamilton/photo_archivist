from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import UUID

from PIL import Image, ImageOps

from app.models import PhotoResult


THUMBNAIL_SIZE = (256, 256)


def _thumbnail_root() -> Path:
    override = os.getenv("PHOTO_ARCHIVIST_THUMBNAIL_DIR")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "photo_archivist" / "thumbnails"


def _scan_directory(scan_id: UUID) -> Path:
    root = _thumbnail_root()
    path = root / str(scan_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_thumbnails_for_results(scan_id: UUID, results: Iterable[PhotoResult]) -> None:
    """Generate thumbnails for each photo result, updating thumbnail metadata in place."""
    target_dir = _scan_directory(scan_id)

    for photo in results:
        destination = target_dir / f"{photo.id}.jpg"

        if destination.exists():
            photo.thumbnail_path = destination
            photo.thumbnail_generated_at = datetime.fromtimestamp(destination.stat().st_mtime, tz=timezone.utc)
            continue

        try:
            _generate_thumbnail(photo, destination)
        except (OSError, ValueError):
            photo.thumbnail_path = None
            photo.thumbnail_generated_at = None
        else:
            photo.thumbnail_path = destination
            photo.thumbnail_generated_at = datetime.now(timezone.utc)


def _generate_thumbnail(photo: PhotoResult, destination: Path) -> None:
    with Image.open(photo.path) as image:
        processed = ImageOps.exif_transpose(image)
        processed = processed.convert("RGB")
        processed.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        processed.save(destination, format="JPEG", optimize=True, quality=85)

