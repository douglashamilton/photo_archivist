from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import imagehash
from PIL import Image


@dataclass(slots=True)
class ScanItem:
    path: Path
    image: Image.Image
    captured_at: datetime
    used_fallback: bool


@dataclass(slots=True)
class QualityAssessment:
    status: str
    notes: list[str]
    metrics: dict[str, float]
    quality_score: float


@dataclass(slots=True)
class ScoreBundle:
    path: Path
    filename: str
    captured_at: datetime
    used_fallback: bool
    metrics: dict[str, float]
    quality: QualityAssessment
    aesthetic: float
    aggregate_score: float


@dataclass(slots=True)
class ScoredItem:
    bundle: ScoreBundle
    phash: imagehash.ImageHash


@dataclass(slots=True)
class ClusteredItem:
    scored: ScoredItem
    cluster_id: str | None = None
    cluster_rank: int | None = None
    cluster_size: int | None = None


def to_photo_score(item: ClusteredItem | ScoredItem) -> dict[str, object]:
    scored = item.scored if isinstance(item, ClusteredItem) else item
    metrics = dict(scored.bundle.metrics)
    metrics.setdefault("aesthetic", scored.bundle.aesthetic)
    return {
        "path": scored.bundle.path,
        "filename": scored.bundle.filename,
        "captured_at": scored.bundle.captured_at,
        "used_fallback": scored.bundle.used_fallback,
        "metrics": metrics,
        "quality_score": scored.bundle.quality.quality_score,
        "quality_status": scored.bundle.quality.status,
        "quality_notes": scored.bundle.quality.notes,
        "score": scored.bundle.aggregate_score,
        "cluster_id": getattr(item, "cluster_id", None),
        "cluster_rank": getattr(item, "cluster_rank", None),
        "cluster_size": getattr(item, "cluster_size", None),
        "phash": str(scored.phash),
    }


def as_iterable(items: Iterable[ClusteredItem | ScoredItem]) -> list[ClusteredItem | ScoredItem]:
    return list(items)
