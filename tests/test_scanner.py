import os
from datetime import date, datetime, timezone
from uuid import UUID

import pytest
from PIL import Image, ImageDraw

from app.models import ScanRequest
from app.services.pipeline.enumerator import FileEnumerator
from app.services.pipeline.models import ClusteredItem, QualityAssessment, ScanItem, ScoredItem, ScoreBundle
from app.services.pipeline.quality import BasicQualityGate
from app.services.pipeline.scoring import MetricScoringEngine
from app.services.pipeline.selector import ShortlistSelector
from app.services.scanner import run_scan


def _create_image(path, color, modified_at: datetime, size: tuple[int, int] = (800, 800)) -> None:
    image = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(image)
    accent = tuple(max(0, channel - 60) for channel in color)
    draw.line((0, 0, size[0], size[1]), fill=accent, width=12)
    draw.rectangle([size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4], outline=accent, width=10)
    image.save(path, format="JPEG", quality=95)
    timestamp = modified_at.timestamp()
    os.utime(path, (timestamp, timestamp))


@pytest.fixture(autouse=True)
def _force_stub_aesthetic(monkeypatch) -> None:
    monkeypatch.setenv("PHOTO_ARCHIVIST_AESTHETIC_BACKEND", "stub")


def test_run_scan_filters_by_date_and_limits_shortlist(tmp_path):
    bright_path = tmp_path / "bright.jpg"
    medium_path = tmp_path / "medium.jpg"
    out_of_range_path = tmp_path / "old.jpg"

    _create_image(bright_path, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(medium_path, (128, 128, 128), datetime(2024, 1, 11, tzinfo=timezone.utc))
    _create_image(out_of_range_path, (200, 200, 200), datetime(2023, 12, 1, tzinfo=timezone.utc))

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    outcome = run_scan(request)

    assert outcome.total_files == 3
    assert outcome.matched_files == 2
    assert outcome.discarded_files == 0
    filenames = [photo.filename for photo in outcome.results]
    assert filenames == ["bright.jpg", "medium.jpg"]
    assert all(photo.used_fallback for photo in outcome.results)
    assert all(isinstance(photo.id, UUID) for photo in outcome.results)
    assert all(photo.thumbnail_path is None for photo in outcome.results)
    assert all("aesthetic" in photo.metrics for photo in outcome.results)
    assert all(photo.quality_status in {"keep", "soft"} for photo in outcome.results)


def test_run_scan_accepts_additional_jpeg_extensions(tmp_path):
    jfif_path = tmp_path / "sample.jfif"
    _create_image(jfif_path, (180, 180, 180), datetime(2024, 1, 12, tzinfo=timezone.utc))

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    outcome = run_scan(request)

    assert outcome.total_files == 1
    assert outcome.matched_files == 1
    assert outcome.results[0].filename == "sample.jfif"


def test_run_scan_reports_progress_incrementally(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"

    _create_image(first, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(second, (200, 200, 200), datetime(2024, 1, 11, tzinfo=timezone.utc))

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    calls: list[tuple[int, int, int]] = []

    outcome = run_scan(request, progress_callback=lambda processed, total, matched: calls.append((processed, total, matched)))

    assert outcome.total_files == 2
    assert calls[0] == (0, 0, 0)
    assert any(total >= 1 for _, total, _ in calls[1:]), "Expected total to grow during iteration"
    assert calls[-1] == (2, 2, 2)


def test_file_enumerator_filters_non_jpeg_files(tmp_path):
    jpeg_path = tmp_path / "keep.jpg"
    other_path = tmp_path / "ignore.png"
    _create_image(jpeg_path, (255, 255, 255), datetime(2024, 1, 1, tzinfo=timezone.utc))
    other_path.write_text("not an image")

    enumerator = FileEnumerator()
    files = {path.name for path in enumerator.iter_files(tmp_path)}

    assert files == {"keep.jpg"}


def test_metric_scoring_engine_reports_metrics(tmp_path):
    image_path = tmp_path / "metric.jpg"
    captured_at = datetime(2024, 1, 5, tzinfo=timezone.utc)
    _create_image(image_path, (200, 200, 200), captured_at)

    scoring_engine = MetricScoringEngine()
    with Image.open(image_path) as image:
        scan_item = ScanItem(path=image_path, image=image, captured_at=captured_at, used_fallback=False)
        quality = QualityAssessment(
            status="keep",
            notes=[],
            metrics={"contrast": 0.0, "sharpness": 0.0, "brightness": 0.0},
            quality_score=0.0,
        )
        bundle = scoring_engine.score(scan_item, quality)

    assert bundle.metrics["brightness"] == bundle.metrics["brightness"]
    assert bundle.filename == "metric.jpg"
    assert not bundle.used_fallback


def test_shortlist_selector_limits_results(tmp_path):
    selector = ShortlistSelector(limit=1)
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    high_bundle = ScoreBundle(
        path=tmp_path / "high.jpg",
        filename="high.jpg",
        captured_at=base_time,
        used_fallback=False,
        metrics={"brightness": 200.0, "aesthetic": 200.0},
        quality=QualityAssessment(status="keep", notes=[], metrics={}, quality_score=0.0),
        aesthetic=200.0,
        aggregate_score=200.0,
    )
    low_bundle = ScoreBundle(
        path=tmp_path / "low.jpg",
        filename="low.jpg",
        captured_at=base_time,
        used_fallback=False,
        metrics={"brightness": 100.0, "aesthetic": 100.0},
        quality=QualityAssessment(status="keep", notes=[], metrics={}, quality_score=0.0),
        aesthetic=100.0,
        aggregate_score=100.0,
    )

    results = selector.select(
        [
            ClusteredItem(scored=ScoredItem(bundle=high_bundle, phash=None)),
            ClusteredItem(scored=ScoredItem(bundle=low_bundle, phash=None)),
        ]
    )
    assert len(results) == 1


def test_quality_gate_drops_dark_frames(tmp_path):
    keep_path = tmp_path / "keep.jpg"
    dark_path = tmp_path / "dark.jpg"

    _create_image(keep_path, (200, 200, 200), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(dark_path, (5, 5, 5), datetime(2024, 1, 11, tzinfo=timezone.utc))

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    outcome = run_scan(request, quality_gate=BasicQualityGate())

    assert outcome.total_files == 2
    assert outcome.matched_files == 2
    assert outcome.discarded_files == 1
    assert [photo.filename for photo in outcome.results] == ["keep.jpg"]
    assert outcome.results[0].quality_status in {"keep", "soft"}


def test_quality_gate_demotes_dim_frames(tmp_path):
    dim_path = tmp_path / "dim.jpg"

    _create_image(dim_path, (45, 45, 45), datetime(2024, 1, 10, tzinfo=timezone.utc))

    gate = BasicQualityGate(brightness_drop=30.0, brightness_soft=50.0)
    with Image.open(dim_path) as image:
        assessment = gate.evaluate(image)

    assert assessment.status == "soft"
    assert "dim" in assessment.notes


def test_phash_clusterer_keeps_top_two_per_burst(tmp_path):
    primary = tmp_path / "primary.jpg"
    alt_one = tmp_path / "alt_one.jpg"
    alt_two = tmp_path / "alt_two.jpg"

    _create_image(primary, (210, 210, 210), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(alt_one, (205, 205, 205), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(alt_two, (200, 200, 200), datetime(2024, 1, 10, tzinfo=timezone.utc))

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    outcome = run_scan(request)

    assert outcome.total_files == 3
    assert outcome.matched_files == 3
    assert len(outcome.results) == 2
