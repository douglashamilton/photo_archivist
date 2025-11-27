from __future__ import annotations

import imagehash

from .interfaces import Clusterer, Hasher
from .models import ClusteredItem, ScoredItem


class PerceptualHasher(Hasher):
    def __init__(self) -> None:
        self._hasher = imagehash.phash

    def hash(self, image) -> imagehash.ImageHash:
        return self._hasher(image)

    @staticmethod
    def distance(first: imagehash.ImageHash, second: imagehash.ImageHash) -> int:
        return int(first - second)


class PhashClusterer(Clusterer):
    def __init__(self, *, distance_threshold: int = 5, keep_per_cluster: int = 2):
        self.distance_threshold = distance_threshold
        self.keep_per_cluster = keep_per_cluster

    def cluster(self, candidates: list[ScoredItem]) -> list[ClusteredItem]:
        if not candidates:
            return []

        clusters: list[list[ScoredItem]] = []
        for candidate in candidates:
            placed = False
            for cluster in clusters:
                if any(PerceptualHasher.distance(candidate.phash, existing.phash) <= self.distance_threshold for existing in cluster):
                    cluster.append(candidate)
                    placed = True
                    break
            if not placed:
                clusters.append([candidate])

        survivors: list[ClusteredItem] = []
        for idx, cluster in enumerate(clusters, start=1):
            cluster_id = f"cluster-{idx}"
            cluster.sort(key=self._sort_key, reverse=True)
            for rank, candidate in enumerate(cluster, start=1):
                item = ClusteredItem(
                    scored=candidate,
                    cluster_id=cluster_id,
                    cluster_rank=rank,
                    cluster_size=len(cluster),
                )
                if rank <= self.keep_per_cluster:
                    survivors.append(item)
        return survivors

    @staticmethod
    def _sort_key(candidate: ScoredItem) -> tuple[float, float, float, float, int]:
        metrics = candidate.bundle.metrics
        sharpness = metrics.get("sharpness", 0.0)
        brightness = metrics.get("brightness", 0.0)
        contrast = metrics.get("contrast", 0.0)
        quality_score = candidate.bundle.quality.quality_score or 0.0
        status_rank = 1 if candidate.bundle.quality.status == "keep" else 0
        return status_rank, quality_score, sharpness, brightness, contrast
