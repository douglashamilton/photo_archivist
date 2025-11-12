from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from PIL import ExifTags, Image, ImageStat, UnidentifiedImageError

from app.models import PhotoResult, ScanOutcome, ScanRequest

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".jpe", ".jfif")

DATETIME_ORIGINAL_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "DateTimeOriginal"), None
)


ProgressCallback = Callable[[int, int, int], None]


def run_scan(request: ScanRequest, progress_callback: Optional[ProgressCallback] = None) -> ScanOutcome:
    """Traverse the directory, filter images by date, and return the top five by brightness."""
    total_files = 0
    processed_files = 0
    matched_files = 0
    shortlist: list[PhotoResult] = []

    if progress_callback:
        progress_callback(processed_files, total_files, matched_files)

    for image_path in _iter_image_files(request.directory):
        total_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

        try:
            result = _process_image(image_path, request.start_date, request.end_date)
        except (UnidentifiedImageError, OSError):
            # Skip files that cannot be read as valid images.
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if result is None:
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        processed_files += 1
        matched_files += 1
        shortlist.append(result)
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

    shortlist.sort(key=lambda item: item.brightness, reverse=True)
    return ScanOutcome(results=shortlist[:5], total_files=total_files, matched_files=matched_files)


def _iter_image_files(directory: Path) -> Iterable[Path]:
    for path in directory.rglob("*"):
        if path.is_file() and _is_allowed_extension(path):
            yield path


def _is_allowed_extension(path: Path) -> bool:
    name = path.name.lower().strip()
    return any(name.endswith(ext) for ext in ALLOWED_EXTENSIONS)


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

    return PhotoResult.create(
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
