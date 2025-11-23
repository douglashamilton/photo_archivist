from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

import cv2
import imagehash
import numpy as np
from PIL import ExifTags, Image, ImageStat, UnidentifiedImageError

from app.models import PhotoResult, PhotoScore, ScanOutcome, ScanRequest

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".jpe", ".jfif")
SHORTLIST_LIMIT = 5

DATETIME_ORIGINAL_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "DateTimeOriginal"), None
)
DEFAULT_AESTHETIC_MODEL = os.getenv("PHOTO_ARCHIVIST_AESTHETIC_MODEL", "cafeai/cafe_aesthetic")


ProgressCallback = Callable[[int, int, int], None]
logger = logging.getLogger(__name__)
_DEFAULT_AESTHETIC_SCORER: "AestheticScoringEngine" | None = None


@dataclass(slots=True)
class QualityAssessment:
    status: str
    notes: list[str]
    metrics: dict[str, float]
    quality_score: float


@dataclass(slots=True)
class ProcessResult:
    in_range: bool
    dropped: bool
    score: PhotoScore | None = None
    phash: imagehash.ImageHash | None = None


@dataclass(slots=True)
class ScanCandidate:
    score: PhotoScore
    phash: imagehash.ImageHash


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
    """Default scoring engine kept for backwards compatibility."""

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
            quality_score=brightness,
        )


class QualityGate:
    """Cheap, CPU-friendly quality checks to drop obvious low-quality frames."""

    def __init__(
        self,
        *,
        brightness_drop: float = 30.0,
        brightness_soft: float = 50.0,
        contrast_drop: float = 10.0,
        blur_drop: float = 50.0,
        blur_soft: float = 120.0,
        min_dimension: int = 600,
        min_aspect: float = 0.33,
        max_aspect: float = 3.0,
    ):
        self.brightness_drop = brightness_drop
        self.brightness_soft = brightness_soft
        self.contrast_drop = contrast_drop
        self.blur_drop = blur_drop
        self.blur_soft = blur_soft
        self.min_dimension = min_dimension
        self.min_aspect = min_aspect
        self.max_aspect = max_aspect

    def evaluate(self, image: Image.Image) -> QualityAssessment:
        grayscale = image.convert("L")
        stats = ImageStat.Stat(grayscale)
        brightness = float(stats.mean[0])
        contrast = float(stats.stddev[0])
        laplacian = cv2.Laplacian(np.array(grayscale), cv2.CV_64F)
        sharpness = float(laplacian.var())
        width, height = image.size
        aspect_ratio = (width / height) if height else 0.0

        status = "keep"
        notes: list[str] = []

        if brightness < self.brightness_drop:
            status = "drop"
            notes.append("dark")
        elif brightness < self.brightness_soft:
            notes.append("dim")

        if contrast < self.contrast_drop:
            status = "drop"
            notes.append("low-contrast")

        if sharpness < self.blur_drop:
            status = "drop"
            notes.append("blurred")
        elif sharpness < self.blur_soft:
            status = "soft" if status != "drop" else status
            notes.append("soft")

        if min(width, height) < self.min_dimension:
            status = "drop"
            notes.append("low-res")

        if aspect_ratio and (aspect_ratio < self.min_aspect or aspect_ratio > self.max_aspect):
            status = "drop"
            notes.append("extreme-aspect")

        quality_score = sharpness + (brightness * 0.1) + (contrast * 0.1)
        if "dim" in notes:
            quality_score -= 5
        quality_score = max(0.0, quality_score)

        effective_status = status
        if status == "keep" and notes:
            effective_status = "soft"

        metrics = {
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": sharpness,
            "width": float(width),
            "height": float(height),
            "aspect_ratio": aspect_ratio,
        }
        return QualityAssessment(status=effective_status, notes=notes, metrics=metrics, quality_score=quality_score)


class PerceptualHasher:
    """Compute perceptual hashes for deduplication."""

    def __init__(self) -> None:
        self._hasher = imagehash.phash

    def hash(self, image: Image.Image) -> imagehash.ImageHash:
        return self._hasher(image)

    @staticmethod
    def distance(first: imagehash.ImageHash, second: imagehash.ImageHash) -> int:
        return int(first - second)


class PhashClusterer:
    """Cluster candidates by perceptual hash and keep the best few per burst."""

    def __init__(self, *, distance_threshold: int = 5, keep_per_cluster: int = 2):
        self.distance_threshold = distance_threshold
        self.keep_per_cluster = keep_per_cluster

    def cluster(self, candidates: list[ScanCandidate]) -> list[ScanCandidate]:
        if not candidates:
            return []

        clusters: list[list[ScanCandidate]] = []
        for candidate in candidates:
            placed = False
            for cluster in clusters:
                if any(PerceptualHasher.distance(candidate.phash, existing.phash) <= self.distance_threshold for existing in cluster):
                    cluster.append(candidate)
                    placed = True
                    break
            if not placed:
                clusters.append([candidate])

        survivors: list[ScanCandidate] = []
        for idx, cluster in enumerate(clusters, start=1):
            cluster_id = f"cluster-{idx}"
            cluster.sort(key=self._sort_key, reverse=True)
            for rank, candidate in enumerate(cluster, start=1):
                candidate.score.cluster_id = cluster_id
                candidate.score.cluster_size = len(cluster)
                candidate.score.cluster_rank = rank
                if rank <= self.keep_per_cluster:
                    survivors.append(candidate)
        return survivors

    @staticmethod
    def _sort_key(candidate: ScanCandidate) -> tuple[float, float, float, float, int]:
        metrics = candidate.score.metrics
        sharpness = metrics.get("sharpness", 0.0)
        brightness = metrics.get("brightness", 0.0)
        contrast = metrics.get("contrast", 0.0)
        quality_score = candidate.score.quality_score or 0.0
        status_rank = 1 if candidate.score.quality_status == "keep" else 0
        return status_rank, quality_score, sharpness, brightness, contrast


class AestheticScoringEngine:
    """Compute a single aesthetic score per image with optional Hugging Face model backing."""

    def __init__(
        self,
        *,
        model_name: str | None = None,
        enabled: bool | None = None,
    ):
        backend = os.getenv("PHOTO_ARCHIVIST_AESTHETIC_BACKEND", "").lower()
        self.use_stub = backend in {"stub", "disabled", "off"}
        if enabled is False:
            self.use_stub = True
        self.model_name = model_name or DEFAULT_AESTHETIC_MODEL
        self._pipeline = None
        self._cache: dict[str, float] = {}

    def score(
        self,
        image_path: Path,
        *,
        metrics: dict[str, float] | None = None,
        image: Image.Image | None = None,
    ) -> float:
        cache_key = self._hash_file(image_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        value: float
        if self.use_stub:
            value = self._stub_score(metrics)
        else:
            try:
                value = self._run_model(image_path, image=image)
            except Exception:  # pragma: no cover - defensive fallback
                logger.exception("Falling back to stub aesthetic scorer for %s", image_path)
                self.use_stub = True
                value = self._stub_score(metrics)

        self._cache[cache_key] = value
        return value

    def _run_model(self, image_path: Path, *, image: Image.Image | None = None) -> float:
        pipeline = self._load_pipeline()
        if pipeline is None:
            return self._stub_score()
        input_image = image if image is not None else Image.open(image_path).convert("RGB")
        outputs = pipeline(input_image)
        if not outputs:
            return 0.0
        raw_score = float(outputs[0].get("score", 0.0))
        return max(0.0, min(10.0, raw_score * (10.0 if raw_score <= 1 else 1.0)))

    def _load_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline
        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover - defensive fallback
            logger.warning("Transformers not available (%s); using stub aesthetic scorer", exc)
            self.use_stub = True
            return None

        self._pipeline = pipeline(
            task="image-classification",
            model=self.model_name,
            device=0 if self._has_gpu() else -1,
        )
        return self._pipeline

    @staticmethod
    def _has_gpu() -> bool:
        try:
            import torch

            return bool(torch.cuda.is_available())
        except Exception:
            return False

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _stub_score(metrics: dict[str, float] | None = None) -> float:
        metrics = metrics or {}
        brightness = metrics.get("brightness", 0.0)
        contrast = metrics.get("contrast", 0.0)
        sharpness = metrics.get("sharpness", 0.0)
        base = (brightness / 255.0) * 4.0 + (contrast / 255.0) * 2.5 + min(sharpness, 300.0) / 60.0
        return max(0.0, min(10.0, base))


class ShortlistSelector:
    """Keeps only the highest-scoring photos."""

    def __init__(self, limit: int = SHORTLIST_LIMIT):
        self.limit = limit
        self._scores: list[PhotoScore] = []

    def consider(self, item: PhotoScore) -> None:
        self._scores.append(item)
        self._scores.sort(key=self._sort_key, reverse=True)
        if len(self._scores) > self.limit:
            self._scores.pop()

    def results(self) -> list[PhotoScore]:
        return list(self._scores)

    @staticmethod
    def _sort_key(score: PhotoScore) -> tuple[float, float, float, float, float, int]:
        metrics = score.metrics or {}
        aesthetic = metrics.get("aesthetic", score.score)
        sharpness = metrics.get("sharpness", 0.0)
        brightness = metrics.get("brightness", 0.0)
        contrast = metrics.get("contrast", 0.0)
        quality_score = score.quality_score or 0.0
        quality_rank = 1 if score.quality_status == "keep" else 0
        return aesthetic, quality_rank, quality_score, sharpness, brightness, contrast


def run_scan(
    request: ScanRequest,
    progress_callback: Optional[ProgressCallback] = None,
    *,
    enumerator: Optional[FileEnumerator] = None,
    metadata_resolver: Optional[MetadataResolver] = None,
    scoring_engine: Optional[BrightnessScoringEngine] = None,
    selector: Optional[ShortlistSelector] = None,
    quality_gate: Optional[QualityGate] = None,
    hasher: Optional[PerceptualHasher] = None,
    clusterer: Optional[PhashClusterer] = None,
    aesthetic_scorer: Optional[AestheticScoringEngine] = None,
) -> ScanOutcome:
    """Traverse the directory, filter images by date/quality, dedupe, and return the top five."""
    enumerator = enumerator or FileEnumerator()
    metadata_resolver = metadata_resolver or MetadataResolver()
    scoring_engine = scoring_engine or BrightnessScoringEngine()
    selector = selector or ShortlistSelector()
    quality_gate = quality_gate or QualityGate()
    hasher = hasher or PerceptualHasher()
    clusterer = clusterer or PhashClusterer()
    global _DEFAULT_AESTHETIC_SCORER
    aesthetic_scorer = aesthetic_scorer or _DEFAULT_AESTHETIC_SCORER or AestheticScoringEngine()
    _DEFAULT_AESTHETIC_SCORER = _DEFAULT_AESTHETIC_SCORER or aesthetic_scorer

    total_files = 0
    processed_files = 0
    matched_files = 0
    discarded_files = 0

    candidates: list[ScanCandidate] = []

    if progress_callback:
        progress_callback(processed_files, total_files, matched_files)

    for image_path in enumerator.iter_files(request.directory):
        total_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

        try:
            result = _process_image(
                image_path=image_path,
                start_date=request.start_date,
                end_date=request.end_date,
                metadata_resolver=metadata_resolver,
                scoring_engine=scoring_engine,
                quality_gate=quality_gate,
                hasher=hasher,
            )
        except (UnidentifiedImageError, OSError):
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if result is None:
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if result.in_range:
            matched_files += 1
        if result.dropped:
            discarded_files += 1
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if result.score is not None and result.phash is not None:
            candidates.append(ScanCandidate(score=result.score, phash=result.phash))

        processed_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

    clustered = clusterer.cluster(candidates)

    for candidate in clustered:
        aesthetic = aesthetic_scorer.score(candidate.score.path, metrics=candidate.score.metrics)
        candidate.score.metrics["aesthetic"] = aesthetic
        candidate.score.score = aesthetic
        selector.consider(candidate.score)

    shortlist = [PhotoResult.from_score(score) for score in selector.results()]
    return ScanOutcome(
        results=shortlist,
        total_files=total_files,
        matched_files=matched_files,
        discarded_files=discarded_files,
    )


def _process_image(
    image_path: Path,
    start_date: date,
    end_date: date,
    metadata_resolver: MetadataResolver,
    scoring_engine: BrightnessScoringEngine,
    quality_gate: QualityGate,
    hasher: PerceptualHasher,
) -> ProcessResult | None:
    with Image.open(image_path) as image:
        captured_at, used_fallback = metadata_resolver.resolve(image_path, image)
        if not _is_within_range(captured_at, start_date, end_date):
            return ProcessResult(in_range=False, dropped=False)

        assessment = quality_gate.evaluate(image)
        metrics = dict(assessment.metrics)

        if assessment.status == "drop":
            return ProcessResult(in_range=True, dropped=True)

        phash_value = hasher.hash(image)

        score = scoring_engine.score(
            image_path=image_path,
            image=image,
            captured_at=captured_at,
            used_fallback=used_fallback,
        )
        score.metrics.update(metrics)
        score.quality_status = assessment.status
        score.quality_notes = assessment.notes
        score.quality_score = assessment.quality_score
        score.phash = str(phash_value)
        return ProcessResult(in_range=True, dropped=False, score=score, phash=phash_value)


def _is_within_range(captured_at: datetime, start_date: date, end_date: date) -> bool:
    capture_date = captured_at.date()
    return start_date <= capture_date <= end_date
