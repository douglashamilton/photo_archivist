from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from PIL import ExifTags, Image

DATETIME_ORIGINAL_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "DateTimeOriginal"), None
)


class MetadataResolver:
    def __init__(self, datetime_tag: int | None = DATETIME_ORIGINAL_TAG):
        self.datetime_tag = datetime_tag

    def resolve(self, image_path: Path, image: Image.Image) -> Tuple[datetime, bool]:
        if self.datetime_tag is not None:
            exif = image.getexif() or {}
            raw_value = exif.get(self.datetime_tag)
            if raw_value:
                parsed = self._parse_exif_datetime(str(raw_value))
                if parsed is not None:
                    return parsed, False

        fallback_datetime = datetime.fromtimestamp(image_path.stat().st_mtime, tz=timezone.utc)
        return fallback_datetime, True

    @staticmethod
    def _parse_exif_datetime(raw: str) -> datetime | None:
        for pattern in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(raw, pattern)
            except ValueError:
                continue
        return None
