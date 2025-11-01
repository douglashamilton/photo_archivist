import asyncio
import os
import re
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.main import app


def _create_image(path, color, modified_at: datetime) -> None:
    image = Image.new("RGB", (16, 16), color=color)
    image.save(path, format="JPEG")
    timestamp = modified_at.timestamp()
    os.utime(path, (timestamp, timestamp))


SCAN_ID_PATTERN = re.compile(r'data-scan-id="([^"]+)"')


def _extract_scan_id(html: str) -> str:
    match = SCAN_ID_PATTERN.search(html)
    assert match, "Expected scan id in HTML payload"
    return match.group(1)


@pytest.mark.asyncio
async def test_get_root_renders_form() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'name="directory"' in html
    assert 'name="start_date"' in html
    assert 'name="end_date"' in html


@pytest.mark.asyncio
async def test_post_scans_returns_polling_partial_and_results(tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    dim_path = tmp_path / "dim.jpg"

    _create_image(bright_path, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(dim_path, (64, 64, 64), datetime(2024, 1, 11, tzinfo=timezone.utc))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/scans",
            data={
                "directory": str(tmp_path),
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 202
        html = response.text
        assert 'data-scan-state="queued"' in html or "Scan in progress" in html
        scan_id = _extract_scan_id(html)

        result_html = None
        for _ in range(10):
            fragment = await client.get(f"/fragments/shortlist/{scan_id}")
            assert fragment.status_code == 200
            fragment_html = fragment.text
            if "Top 2 photos" in fragment_html:
                result_html = fragment_html
                break
            await asyncio.sleep(0.05)

        assert result_html is not None, "Polling did not yield final results"
        assert "Matched 2 of 2 JPEG files." in result_html
        assert "bright.jpg" in result_html
        assert "dim.jpg" in result_html


@pytest.mark.asyncio
async def test_post_scans_with_invalid_directory_returns_error(tmp_path) -> None:
    invalid_directory = tmp_path / "missing"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/scans",
            data={
                "directory": str(invalid_directory),
                "start_date": "2024-01-01",
                "end_date": "2024-01-10",
            },
            headers={"HX-Request": "true"},
        )

    assert response.status_code == 422
    assert "Directory does not exist." in response.text


@pytest.mark.asyncio
async def test_post_scans_without_htmx_returns_full_page(tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    _create_image(bright_path, (200, 200, 200), datetime(2024, 1, 10, tzinfo=timezone.utc))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/scans",
            data={
                "directory": str(tmp_path),
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )

        assert response.status_code == 202
        html = response.text
        assert "<form" in html
        assert 'value="' + str(tmp_path) + '"' in html
        assert "Scan in progress" in html or 'data-scan-state="queued"' in html

        scan_id = _extract_scan_id(html)

        for _ in range(10):
            fragment = await client.get(f"/fragments/shortlist/{scan_id}")
            if "Top 1 photo" in fragment.text or "Top 1 photos" in fragment.text:
                assert "bright.jpg" in fragment.text
                break
            await asyncio.sleep(0.05)
        else:
            pytest.fail("Scan did not complete within expected time")


@pytest.mark.asyncio
async def test_api_scan_status_endpoint_returns_json(tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    _create_image(bright_path, (220, 220, 220), datetime(2024, 1, 12, tzinfo=timezone.utc))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        post_response = await client.post(
            "/api/scans",
            data={
                "directory": str(tmp_path),
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
            headers={"accept": "application/json"},
        )

        assert post_response.status_code == 202
        payload = post_response.json()
        scan_id = payload["id"]
        assert payload["state"] in {"queued", "running"}

        for _ in range(10):
            status_response = await client.get(f"/api/scans/{scan_id}")
            assert status_response.status_code == 200
            status_payload = status_response.json()
            if status_payload["state"] == "complete":
                break
            await asyncio.sleep(0.05)
        else:
            pytest.fail("Scan did not reach completion")

        assert status_payload["summary"]["matched_files"] == 1
        assert status_payload["results"][0]["filename"] == "bright.jpg"
