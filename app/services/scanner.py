from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Sequence

from PIL import Image, UnidentifiedImageError

from app.models import PhotoResult, PhotoScore, ScanOutcome, ScanRequest
from app.services.config import ScanConfig
from app.services.pipeline.dedupe import PerceptualHasher, PhashClusterer
from app.services.pipeline.enumerator import FileEnumerator
from app.services.pipeline.interfaces import (
    Clusterer,
    Enumerator,
    Hasher,
    MetadataResolverProtocol,
    ProgressCallback,
    QualityGate,
    ScoringEngine,
    Selector,
)
from app.services.pipeline.metadata import MetadataResolver
from app.services.pipeline.models import ClusteredItem, ScanItem, ScoredItem, to_photo_score
from app.services.pipeline.quality import BasicQualityGate
from app.services.pipeline.scoring import AestheticScoringEngine, MetricScoringEngine
from app.services.pipeline.selector import ShortlistSelector

logger = logging.getLogger(__name__)


def run_scan(
    request: ScanRequest,
    progress_callback: Optional[ProgressCallback] = None,
    *,
    config: Optional[ScanConfig] = None,
    enumerator: Optional[Enumerator] = None,
    metadata_resolver: Optional[MetadataResolver] = None,
    scoring_engine: Optional[ScoringEngine] = None,
    selector: Optional[Selector] = None,
    quality_gate: Optional[QualityGate] = None,
    hasher: Optional[Hasher] = None,
    clusterer: Optional[Clusterer] = None,
    aesthetic_scorer: Optional[AestheticScoringEngine] = None,
) -> ScanOutcome:
    config = config or ScanConfig.from_env()

    enumerator = enumerator or FileEnumerator(config.allowed_extensions)
    metadata_resolver = metadata_resolver or MetadataResolver()
    quality_gate = quality_gate or BasicQualityGate(
        brightness_drop=config.brightness_drop,
        brightness_soft=config.brightness_soft,
        contrast_drop=config.contrast_drop,
        blur_drop=config.blur_drop,
        blur_soft=config.blur_soft,
        min_dimension=config.min_dimension,
        min_aspect=config.min_aspect,
        max_aspect=config.max_aspect,
    )
    hasher = hasher or PerceptualHasher()
    scoring_engine = scoring_engine or MetricScoringEngine(
        aesthetic_scorer=aesthetic_scorer
        or AestheticScoringEngine(model_name=config.aesthetic_model, backend=config.aesthetic_backend)
    )
    clusterer = clusterer or PhashClusterer(
        distance_threshold=config.distance_threshold, keep_per_cluster=config.keep_per_cluster
    )
    selector = selector or ShortlistSelector(limit=config.shortlist_limit)

    total_files = 0
    processed_files = 0
    matched_files = 0
    discarded_files = 0

    scored_items: list[ScoredItem] = []

    if progress_callback:
        progress_callback(processed_files, total_files, matched_files)

    for image_path in enumerator.iter_files(request.directory):
        total_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

        try:
            item_result = _process_image(
                image_path=image_path,
                start_date=request.start_date,
                end_date=request.end_date,
                metadata_resolver=metadata_resolver,
                quality_gate=quality_gate,
                hasher=hasher,
                scoring_engine=scoring_engine,
            )
        except (UnidentifiedImageError, OSError):
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if item_result is None:
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        matched_files += 1

        if isinstance(item_result, bool):
            processed_files += 1
            if not item_result:
                discarded_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, matched_files)
            continue

        if isinstance(item_result, ScoredItem):
            scored_items.append(item_result)

        processed_files += 1
        if progress_callback:
            progress_callback(processed_files, total_files, matched_files)

    clustered = clusterer.cluster(scored_items)
    shortlist_candidates = selector.select(clustered)
    shortlist = _to_photo_results(shortlist_candidates)

    if config.debug_report:
        _write_debug_report(
            config.debug_dir,
            clustered,
        )

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
    quality_gate: QualityGate,
    hasher: Hasher,
    scoring_engine: ScoringEngine,
) -> ScoredItem | bool | None:
    with Image.open(image_path) as image:
        captured_at, used_fallback = metadata_resolver.resolve(image_path, image)
        working_image = image.convert("RGB")
        if not _is_within_range(captured_at, start_date, end_date):
            return None

        assessment = quality_gate.evaluate(working_image)
        if assessment.status == "drop":
            return False

        phash_value = hasher.hash(working_image)

        scan_item = ScanItem(
            path=image_path,
            image=working_image,
            captured_at=captured_at,
            used_fallback=used_fallback,
        )
        bundle = scoring_engine.score(scan_item, assessment)
        return ScoredItem(bundle=bundle, phash=phash_value)


def _to_photo_results(items: Sequence[ClusteredItem | ScoredItem]) -> list[PhotoResult]:
    results: list[PhotoResult] = []
    for idx, item in enumerate(items, start=1):
        score_payload: dict = to_photo_score(item)
        photo_score = PhotoScore(**score_payload)
        results.append(PhotoResult.from_score(photo_score))
    return results


def _write_debug_report(directory: str, items: list[ClusteredItem]) -> None:
    Path(directory).mkdir(parents=True, exist_ok=True)
    serialisable = []
    for rank, item in enumerate(items, start=1):
        payload = to_photo_score(item)
        payload["rank"] = rank
        serialisable.append(payload)
    output = Path(directory) / f"scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}-scores.json"
    output.write_text(json.dumps(serialisable, default=str, indent=2))


def _is_within_range(captured_at: datetime, start_date: date, end_date: date) -> bool:
    capture_date = captured_at.date()
    return start_date <= capture_date <= end_date
