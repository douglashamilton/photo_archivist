from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable, Callable

import imagehash
from PIL import Image

from .models import ClusteredItem, QualityAssessment, ScanItem, ScoreBundle, ScoredItem

ProgressCallback = Callable[[int, int, int], None]


@runtime_checkable
class Enumerator(Protocol):
    def iter_files(self, directory) -> Iterable: ...


@runtime_checkable
class MetadataResolverProtocol(Protocol):
    def resolve(self, image_path, image: Image.Image): ...


@runtime_checkable
class QualityGate(Protocol):
    def evaluate(self, image: Image.Image) -> QualityAssessment: ...


@runtime_checkable
class Hasher(Protocol):
    def hash(self, image: Image.Image) -> imagehash.ImageHash: ...


@runtime_checkable
class Clusterer(Protocol):
    def cluster(self, candidates: list[ScoredItem]) -> list[ClusteredItem]: ...


@runtime_checkable
class ScoringEngine(Protocol):
    def score(self, item: ScanItem, quality: QualityAssessment) -> ScoreBundle: ...


@runtime_checkable
class Selector(Protocol):
    def select(self, items: Iterable[ClusteredItem | ScoredItem]) -> list[ClusteredItem | ScoredItem]: ...
