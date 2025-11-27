from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from PIL import Image, ImageStat

from .interfaces import ScoringEngine
from .models import QualityAssessment, ScanItem, ScoreBundle

logger = logging.getLogger(__name__)


class AestheticScoringEngine:
    def __init__(self, *, model_name: str | None = None, backend: str | None = None, enabled: bool | None = None):
        backend = (backend or os.getenv("PHOTO_ARCHIVIST_AESTHETIC_BACKEND", "")).lower()
        self.use_stub = backend in {"stub", "disabled", "off"}
        if enabled is False:
            self.use_stub = True
        self.model_name = model_name or os.getenv("PHOTO_ARCHIVIST_AESTHETIC_MODEL", "cafeai/cafe_aesthetic")
        self._pipeline = None
        self._cache: dict[str, float] = {}

    def score(self, image_path: Path, *, metrics: dict[str, float] | None = None, image: Image.Image | None = None) -> float:
        cache_key = self._hash_file(image_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        value: float
        if self.use_stub:
            value = self._stub_score(metrics)
        else:
            try:
                value = self._run_model(image_path, image=image)
            except Exception:
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


class MetricScoringEngine(ScoringEngine):
    def __init__(self, aesthetic_scorer: AestheticScoringEngine | None = None):
        self.aesthetic_scorer = aesthetic_scorer or AestheticScoringEngine()

    def score(self, item: ScanItem, quality: QualityAssessment) -> ScoreBundle:
        grayscale = item.image.convert("L")
        brightness = float(ImageStat.Stat(grayscale).mean[0])
        metrics = {"brightness": brightness}
        metrics.update(quality.metrics)
        aesthetic = self.aesthetic_scorer.score(item.path, metrics=metrics, image=item.image)
        metrics["aesthetic"] = aesthetic
        aggregate_score = aesthetic
        return ScoreBundle(
            path=item.path,
            filename=item.path.name,
            captured_at=item.captured_at,
            used_fallback=item.used_fallback,
            metrics=metrics,
            quality=quality,
            aesthetic=aesthetic,
            aggregate_score=aggregate_score,
        )
