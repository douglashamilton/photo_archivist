from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageStat

from .interfaces import QualityGate
from .models import QualityAssessment


class BasicQualityGate(QualityGate):
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
            if status != "drop":
                status = "soft"
            notes.append("low-contrast")

        if sharpness < self.blur_drop:
            status = "drop"
            notes.append("blurred")
        elif sharpness < self.blur_soft:
            if status != "drop":
                status = "soft"
            notes.append("soft")

        if min(width, height) < self.min_dimension:
            status = "drop"
            notes.append("low-res")

        if aspect_ratio and (aspect_ratio < self.min_aspect or aspect_ratio > self.max_aspect):
            status = "drop"
            notes.append("extreme-aspect")

        if status == "keep" and any(flag in notes for flag in ("dim", "soft")):
            status = "soft"

        quality_score = sharpness + (brightness * 0.1) + (contrast * 0.1)
        if "dim" in notes:
            quality_score -= 5
        quality_score = max(0.0, quality_score)

        metrics = {
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": sharpness,
            "width": float(width),
            "height": float(height),
            "aspect_ratio": aspect_ratio,
        }

        return QualityAssessment(status=status, notes=notes, metrics=metrics, quality_score=quality_score)
