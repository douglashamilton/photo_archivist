from __future__ import annotations

from typing import Iterable

from .interfaces import Selector
from .models import ClusteredItem, ScoredItem


class ShortlistSelector(Selector):
    def __init__(self, limit: int = 5):
        self.limit = limit

    def select(self, items: Iterable[ClusteredItem | ScoredItem]) -> list[ClusteredItem | ScoredItem]:
        ordered = sorted(items, key=self._sort_key, reverse=True)
        return ordered[: self.limit]

    @staticmethod
    def _sort_key(item: ClusteredItem | ScoredItem) -> tuple[float, float, float, float, float, int]:
        scored = item.scored if isinstance(item, ClusteredItem) else item
        metrics = scored.bundle.metrics or {}
        aesthetic = metrics.get("aesthetic", scored.bundle.aggregate_score)
        sharpness = metrics.get("sharpness", 0.0)
        brightness = metrics.get("brightness", 0.0)
        contrast = metrics.get("contrast", 0.0)
        quality_score = scored.bundle.quality.quality_score or 0.0
        quality_rank = 1 if scored.bundle.quality.status == "keep" else 0
        return aesthetic, quality_rank, quality_score, sharpness, brightness, contrast
