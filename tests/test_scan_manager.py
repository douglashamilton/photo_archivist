import asyncio
import os
from datetime import date, datetime, timezone

import pytest
from PIL import Image

from app.models import ScanRequest, ScanState
from app.services.scan_manager import ScanManager


def _create_image(path, color, modified_at: datetime) -> None:
    image = Image.new("RGB", (16, 16), color=color)
    image.save(path, format="JPEG")
    timestamp = modified_at.timestamp()
    os.utime(path, (timestamp, timestamp))


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
