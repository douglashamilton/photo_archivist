import asyncio
import os
from datetime import date, datetime, timezone

import pytest
from PIL import Image

from app.models import ScanRequest, ScanState
from app.services.scan_manager import ScanManager
from app.services.thumbnails import thumbnail_directory


def _create_image(path, color, modified_at: datetime) -> None:
    image = Image.new("RGB", (16, 16), color=color)
    image.save(path, format="JPEG")
    timestamp = modified_at.timestamp()
    os.utime(path, (timestamp, timestamp))


async def _wait_for_completion(manager: ScanManager, scan_id) -> None:
    for _ in range(60):
        status, _ = manager.snapshot(scan_id)
        if status and status.state == ScanState.COMPLETE:
            return
        await asyncio.sleep(0.05)
    raise AssertionError("Scan did not complete in time")


@pytest.mark.asyncio
async def test_scan_manager_updates_status_incrementally(tmp_path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    _create_image(first, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(second, (200, 200, 200), datetime(2024, 1, 11, tzinfo=timezone.utc))

    manager = ScanManager(max_workers=1)

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    scan_id = manager.enqueue(request)

    totals_seen: list[int] = []
    for _ in range(40):
        status, _ = manager.snapshot(scan_id)
        if status:
            totals_seen.append(status.total)
            if status.state == ScanState.COMPLETE:
                break
        await asyncio.sleep(0.05)

    assert any(total >= 1 for total in totals_seen[1:]), "Expected total count to increase during scan"
    assert totals_seen[-1] == 2
    manager.shutdown()


@pytest.mark.asyncio
async def test_scan_manager_prunes_old_scans_and_thumbnails(tmp_path) -> None:
    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    _create_image(first, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(second, (200, 200, 200), datetime(2024, 1, 11, tzinfo=timezone.utc))

    manager = ScanManager(max_workers=1, history_limit=1)

    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    first_scan = manager.enqueue(request)
    await _wait_for_completion(manager, first_scan)
    first_thumb_dir = thumbnail_directory(first_scan)
    assert first_thumb_dir.exists()

    second_scan = manager.enqueue(request)
    await _wait_for_completion(manager, second_scan)

    assert manager.get_outcome(first_scan) is None
    for _ in range(20):
        if not first_thumb_dir.exists():
            break
        await asyncio.sleep(0.05)
    assert not first_thumb_dir.exists()
    assert manager.get_outcome(second_scan) is not None
    manager.shutdown()


@pytest.mark.asyncio
async def test_scan_manager_shutdown_releases_thumbnails(tmp_path) -> None:
    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    photo_path = tmp_path / "photo.jpg"
    _create_image(photo_path, (220, 220, 220), datetime(2024, 1, 12, tzinfo=timezone.utc))

    manager = ScanManager(max_workers=1, history_limit=5)
    request = ScanRequest(
        directory=tmp_path,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )
    scan_id = manager.enqueue(request)
    await _wait_for_completion(manager, scan_id)

    thumb_dir = thumbnail_directory(scan_id)
    assert thumb_dir.exists()

    manager.shutdown()

    assert not thumb_dir.exists()
    assert manager.get_status(scan_id) is None
