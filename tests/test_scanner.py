import os
from datetime import date, datetime, timezone

from PIL import Image

from app.models import ScanRequest
from app.services.scanner import run_scan


def _create_image(path, color, modified_at: datetime) -> None:
    image = Image.new("RGB", (16, 16), color=color)
    image.save(path, format="JPEG")
    timestamp = modified_at.timestamp()
    os.utime(path, (timestamp, timestamp))


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
    filenames = [photo.filename for photo in outcome.results]
    assert filenames == ["bright.jpg", "medium.jpg"]
    assert all(photo.used_fallback for photo in outcome.results)
    assert outcome.results[0].brightness > outcome.results[1].brightness


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
