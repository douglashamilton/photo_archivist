from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from PIL import ExifTags, Image, ImageStat, UnidentifiedImageError

from app.models import PhotoResult, PhotoScore, ScanOutcome, ScanRequest

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".jpe", ".jfif")
SHORTLIST_LIMIT = 5

DATETIME_ORIGINAL_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "DateTimeOriginal"), None
)


ProgressCallback = Callable[[int, int, int], None]


class FileEnumerator:
    """Walk directories and yield files that match the configured extension list."""

    def __init__(self, allowed_extensions: Iterable[str] = ALLOWED_EXTENSIONS):
        self.allowed_extensions = tuple(ext.lower() for ext in allowed_extensions)

    def iter_files(self, directory: Path) -> Iterable[Path]:
        for path in directory.rglob("*"):
            if path.is_file() and self._is_allowed_extension(path):
                yield path

    def _is_allowed_extension(self, path: Path) -> bool:
        name = path.name.lower().strip()
        return any(name.endswith(ext) for ext in self.allowed_extensions)


class MetadataResolver:
    """Extract capture timestamps from EXIF when possible, falling back to file stats."""

    def __init__(self, datetime_tag: int | None = DATETIME_ORIGINAL_TAG):
        self.datetime_tag = datetime_tag

    def resolve(self, image_path: Path, image: Image.Image) -> tuple[datetime, bool]:
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


class BrightnessScoringEngine:
    """Default scoring engine that tracks mean luminance."""

    metric_name = "brightness"

    def score(
        self,
        image_path: Path,
        image: Image.Image,
        captured_at: datetime,
        used_fallback: bool,
    ) -> PhotoScore:
        grayscale = image.convert("L")
        brightness = float(ImageStat.Stat(grayscale).mean[0])
        metrics = {self.metric_name: brightness}
        return PhotoScore(
            path=image_path,
            filename=image_path.name,
            captured_at=captured_at,
            used_fallback=used_fallback,
            score=brightness,
            metrics=metrics,
        )


class ShortlistSelector:
    """Keeps only the highest-scoring photos."""

    def __init__(self, limit: int = SHORTLIST_LIMIT):
        self.limit = limit
        self._scores: list[PhotoScore] = []

    def consider(self, item: PhotoScore) -> None:
        self._scores.append(item)
        self._scores.sort(key=lambda score: score.score, reverse=True)
        if len(self._scores) > self.limit:
            self._scores.pop()

    def results(self) -> list[PhotoScore]:
        return list(self._scores)


def run_scan(
    request: ScanRequest,
    progress_callback: Optional[ProgressCallback] = None,
    *,
    enumerator: Optional[FileEnumerator] = None,
    metadata_resolver: Optional[MetadataResolver] = None,
    scoring_engine: Optional[BrightnessScoringEngine] = None,
    selector: Optional[ShortlistSelector] = None,
) -> ScanOutcome:
    """Traverse the directory, filter images by date, and return the top five by score."""
    enumerator = enumerator or FileEnumerator()
    metadata_resolver = metadata_resolver or MetadataResolver()
    scoring_engine = scoring_engine or BrightnessScoringEngine()
    selector = selector or ShortlistSelector()

    total_files = 0
    processed_files = 0
    matched_files = 0

    if progress_callback:
        progress_callback(processed_files, total_files, matched_files)

    for image_path in enumerator.iter_files(request.directory):
        total_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

        try:
            score = _process_image(
                image_path=image_path,
                start_date=request.start_date,
                end_date=request.end_date,
                metadata_resolver=metadata_resolver,
                scoring_engine=scoring_engine,
            )
        except (UnidentifiedImageError, OSError):
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if score is None:
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        processed_files += 1
        matched_files += 1
        selector.consider(score)
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

    shortlist = [PhotoResult.from_score(score) for score in selector.results()]
    return ScanOutcome(results=shortlist, total_files=total_files, matched_files=matched_files)


def _process_image(
    image_path: Path,
    start_date: date,
    end_date: date,
    metadata_resolver: MetadataResolver,
    scoring_engine: BrightnessScoringEngine,
) -> PhotoScore | None:
    with Image.open(image_path) as image:
        captured_at, used_fallback = metadata_resolver.resolve(image_path, image)
        if not _is_within_range(captured_at, start_date, end_date):
            return None

        return scoring_engine.score(
            image_path=image_path,
            image=image,
            captured_at=captured_at,
            used_fallback=used_fallback,
        )


def _is_within_range(captured_at: datetime, start_date: date, end_date: date) -> bool:
    capture_date = captured_at.date()
    return start_date <= capture_date <= end_date
