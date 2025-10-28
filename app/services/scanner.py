from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

from PIL import ExifTags, Image, ImageStat, UnidentifiedImageError

from app.models import PhotoResult, ScanOutcome, ScanRequest

ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}

DATETIME_ORIGINAL_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "DateTimeOriginal"), None
)


def run_scan(request: ScanRequest) -> ScanOutcome:
    """Traverse the directory, filter images by date, and return the top five by brightness."""
    total_files = 0
    matched_files = 0
    shortlist: list[PhotoResult] = []

    for image_path in _iter_image_files(request.directory):
        total_files += 1
        try:
            result = _process_image(image_path, request.start_date, request.end_date)
        except (UnidentifiedImageError, OSError):
            # Skip files that cannot be read as valid images.
            continue

        if result is None:
            continue

        matched_files += 1
        shortlist.append(result)

    shortlist.sort(key=lambda item: item.brightness, reverse=True)
    return ScanOutcome(results=shortlist[:5], total_files=total_files, matched_files=matched_files)


def _iter_image_files(directory: Path) -> Iterable[Path]:
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            yield path


def _process_image(
    image_path: Path,
    start_date: date,
    end_date: date,
) -> PhotoResult | None:
    with Image.open(image_path) as image:
        captured_at, used_fallback = _resolve_capture_datetime(image_path, image)
        if captured_at.date() < start_date or captured_at.date() > end_date:
            return None

        grayscale = image.convert("L")
        brightness = float(ImageStat.Stat(grayscale).mean[0])

    return PhotoResult(
        path=image_path,
        filename=image_path.name,
        captured_at=captured_at,
        brightness=brightness,
        used_fallback=used_fallback,
    )


def _resolve_capture_datetime(image_path: Path, image: Image.Image) -> tuple[datetime, bool]:
    if DATETIME_ORIGINAL_TAG is not None:
        exif = image.getexif() or {}
        raw_value = exif.get(DATETIME_ORIGINAL_TAG)
        if raw_value:
            parsed = _parse_exif_datetime(str(raw_value))
            if parsed is not None:
                return parsed, False

    fallback_datetime = datetime.fromtimestamp(image_path.stat().st_mtime, tz=timezone.utc)
    return fallback_datetime, True


def _parse_exif_datetime(raw: str) -> datetime | None:
    for pattern in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, pattern)
        except ValueError:
            continue
    return None
