import os
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
async def test_post_scans_returns_shortlist_partial(tmp_path) -> None:
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

    assert response.status_code == 200
    html = response.text
    assert "Top 2 photos" in html
    assert "Matched 2 of 2 JPEG files." in html
    assert "bright.jpg" in html
    assert "dim.jpg" in html


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

    assert response.status_code == 200
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

    assert response.status_code == 200
    html = response.text
    assert "<form" in html
    assert 'value="' + str(tmp_path) + '"' in html
    assert "Top 1 photos" in html or "Top 1 photo" in html
