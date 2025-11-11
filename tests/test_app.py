import asyncio
import json
import os
import re
from datetime import datetime, timezone

import httpx
import pytest
from httpx import ASGITransport, AsyncClient, MockTransport
from PIL import Image

from app.main import app, print_order_service
from app.services import print_orders
from urllib.parse import urlencode


def _create_image(path, color, modified_at: datetime) -> None:
    image = Image.new("RGB", (16, 16), color=color)
    image.save(path, format="JPEG")
    timestamp = modified_at.timestamp()
    os.utime(path, (timestamp, timestamp))


SCAN_ID_PATTERN = re.compile(r'data-scan-id="([^"]+)"')
THUMBNAIL_SRC_PATTERN = re.compile(r'src="/api/thumbnails/([^/]+)/([^"]+)"')
SELECTION_FORM_PATTERN = re.compile(r'action="/api/scans/([^/]+)/photos/([^/]+)/selection"')


def _extract_scan_id(html: str) -> str:
    match = SCAN_ID_PATTERN.search(html)
    assert match, "Expected scan id in HTML payload"
    return match.group(1)


async def _complete_scan(client: AsyncClient, directory: os.PathLike[str] | str) -> tuple[str, list[dict[str, object]]]:
    response = await client.post(
        "/api/scans",
        data={
            "directory": str(directory),
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 202
    scan_id = _extract_scan_id(response.text)

    for _ in range(30):
        status_response = await client.get(f"/api/scans/{scan_id}")
        assert status_response.status_code == 200
        payload = status_response.json()
        if payload["state"] == "complete":
            return scan_id, payload["results"]
        await asyncio.sleep(0.05)

    raise AssertionError("Scan did not complete in time")


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

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
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
        assert '/api/thumbnails/' in result_html

        thumb_match = THUMBNAIL_SRC_PATTERN.search(result_html)
        assert thumb_match, "Expected thumbnail src in HTML fragment"
        thumb_scan_id, photo_id = thumb_match.groups()
        assert thumb_scan_id == scan_id

        thumbnail_url = f"/api/thumbnails/{thumb_scan_id}/{photo_id}"
        thumbnail_response = await client.get(thumbnail_url)
        assert thumbnail_response.status_code == 200
        assert thumbnail_response.headers["content-type"] == "image/jpeg"


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

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
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
                assert '/api/thumbnails/' in fragment.text
                break
            await asyncio.sleep(0.05)
        else:
            pytest.fail("Scan did not complete within expected time")


@pytest.mark.asyncio
async def test_toggle_selection_updates_html_and_json(tmp_path) -> None:
    photo_path = tmp_path / "photo.jpg"
    _create_image(photo_path, (180, 180, 180), datetime(2024, 1, 10, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        post_response = await client.post(
            "/api/scans",
            data={
                "directory": str(tmp_path),
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
            headers={"HX-Request": "true"},
        )
        assert post_response.status_code == 202
        scan_id = _extract_scan_id(post_response.text)

        for _ in range(10):
            fragment = await client.get(f"/fragments/shortlist/{scan_id}")
            if "Top 1 photo" in fragment.text or "Top 1 photos" in fragment.text:
                shortlist_html = fragment.text
                break
            await asyncio.sleep(0.05)
        else:
            pytest.fail("Scan did not complete in time")

        form_match = SELECTION_FORM_PATTERN.search(shortlist_html)
        assert form_match, "Expected selection form in shortlist"
        action_scan_id, photo_id = form_match.groups()
        assert action_scan_id == scan_id

        select_response = await client.post(
            f"/api/scans/{scan_id}/photos/{photo_id}/selection",
            data={"selected": "true"},
            headers={"HX-Request": "true"},
        )
        assert select_response.status_code == 200
        assert "Selected</span>" in select_response.text
        assert 'aria-pressed="true"' in select_response.text

        deselect_response = await client.post(
            f"/api/scans/{scan_id}/photos/{photo_id}/selection",
            data={"selected": "false"},
            headers={"accept": "application/json"},
        )
        assert deselect_response.status_code == 200
        payload = deselect_response.json()
        assert payload["state"] == "complete"
        assert payload["results"][0]["selected"] is False


@pytest.mark.asyncio
async def test_api_scan_status_endpoint_returns_json(tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    _create_image(bright_path, (220, 220, 220), datetime(2024, 1, 12, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
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
        assert status_payload["results"][0]["thumbnail_url"] is not None
        assert status_payload["results"][0]["selected"] is False


@pytest.mark.asyncio
async def test_post_prints_accepts_json_payload(tmp_path) -> None:
    photo_path = tmp_path / "printable.jpg"
    _create_image(photo_path, (180, 180, 180), datetime(2024, 1, 15, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        scan_id, results = await _complete_scan(client, tmp_path)
        assert results, "Expected at least one shortlist result"
        photo_id = results[0]["id"]

        toggle_response = await client.post(
            f"/api/scans/{scan_id}/photos/{photo_id}/selection",
            data={"selected": "true"},
        )
        assert toggle_response.status_code == 200

        captured_payloads: list[dict[str, object]] = []
        captured_headers: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            captured_payloads.append(json.loads(request.content.decode()))
            captured_headers.append(request.headers.get("x-api-key", ""))
            return httpx.Response(202, json={"id": "PO-12345", "status": "submitted"})

        mock_client = httpx.AsyncClient(transport=MockTransport(handler), base_url="https://api.sandbox.prodigi.com/v4.0")
        print_order_service._http_client = mock_client

        try:
            response = await client.post(
                "/api/prints",
                json={
                    "scan_id": scan_id,
                    "photo_ids": [photo_id],
                    "recipient": {
                        "name": "Ada Lovelace",
                        "email": "ada@example.com",
                        "address": {
                            "line1": "1 Example Street",
                            "city": "London",
                            "state": "London",
                            "postal_code": "N1",
                            "country_code": "GB",
                        },
                    },
                    "shipping_method": "STANDARD",
                    "copies": 2,
                    "asset_base_url": "https://assets.example.com",
                    "api_key": "test-api-key",
                },
            )
        finally:
            await mock_client.aclose()
            print_order_service._http_client = None

        assert response.status_code == 202
        body = response.json()
        assert body["orderId"] == "PO-12345"
        assert captured_payloads, "Prodigi handler was not invoked"
        submitted_payload = captured_payloads[0]
        assert submitted_payload["shippingMethod"] == "Standard"
        asset_url = submitted_payload["items"][0]["assets"][0]["url"]
        assert asset_url.startswith("https://assets.example.com/")
        assert str(photo_id) in asset_url
        assert captured_headers and captured_headers[0] == "test-api-key"


@pytest.mark.asyncio
async def test_post_prints_json_error_includes_debug(tmp_path) -> None:
    photo_path = tmp_path / "printable.jpg"
    _create_image(photo_path, (180, 180, 180), datetime(2024, 1, 15, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        scan_id, results = await _complete_scan(client, tmp_path)
        assert results, "Expected at least one shortlist result"
        photo_id = results[0]["id"]

        toggle_response = await client.post(
            f"/api/scans/{scan_id}/photos/{photo_id}/selection",
            data={"selected": "true"},
        )
        assert toggle_response.status_code == 200

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"Outcome": "NotAuthenticated", "TraceParent": "trace-123"})

        mock_client = httpx.AsyncClient(transport=MockTransport(handler), base_url="https://api.sandbox.prodigi.com/v4.0")
        print_order_service._http_client = mock_client

        try:
            response = await client.post(
                "/api/prints",
                json={
                    "scan_id": scan_id,
                    "photo_ids": [photo_id],
                    "recipient": {
                        "name": "Ada Lovelace",
                        "email": "ada@example.com",
                        "address": {
                            "line1": "1 Example Street",
                            "city": "London",
                            "state": "London",
                            "postal_code": "N1",
                            "country_code": "GB",
                        },
                    },
                    "shipping_method": "STANDARD",
                    "copies": 2,
                    "asset_base_url": "https://assets.example.com",
                    "api_key": "bad-api-key",
                },
            )
        finally:
            await mock_client.aclose()
            print_order_service._http_client = None

        assert response.status_code == 502
        payload = response.json()
        assert payload["status"] == "error"
        assert payload["debug"]["response"]["status_code"] == 401
        assert payload["debug"]["request"]["shippingMethod"] == "Standard"
        assert payload["debug"]["response"]["json"]["Outcome"] == "NotAuthenticated"


@pytest.mark.asyncio
async def test_post_prints_form_submission_returns_success_partial(tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    darker_path = tmp_path / "dark.jpg"
    _create_image(bright_path, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(darker_path, (120, 120, 120), datetime(2024, 1, 11, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        scan_id, results = await _complete_scan(client, tmp_path)
        for result in results:
            toggle_response = await client.post(
                f"/api/scans/{scan_id}/photos/{result['id']}/selection",
                data={"selected": "true"},
                headers={"HX-Request": "true"},
            )
            assert toggle_response.status_code == 200

        captured_payloads: list[dict[str, object]] = []
        captured_headers: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            captured_payloads.append(json.loads(request.content.decode()))
            captured_headers.append(request.headers.get("x-api-key", ""))
            return httpx.Response(202, json={"id": "PO-22222", "status": "submitted"})

        mock_client = httpx.AsyncClient(transport=MockTransport(handler), base_url="https://api.sandbox.prodigi.com/v4.0")
        print_order_service._http_client = mock_client

        try:
            form_entries: list[tuple[str, str]] = [
                ("scan_id", scan_id),
                ("name", "Grace Hopper"),
                ("email", "grace@example.com"),
                ("line1", "2 Example Road"),
                ("line2", ""),
                ("city", "New York"),
                ("state", "NY"),
                ("postal_code", "10001"),
                ("country_code", "US"),
                ("shipping_method", "STANDARD"),
                ("copies", "1"),
                ("asset_base_url", "https://assets.example.com"),
                ("api_key", "  example-key  "),
            ]
            for result in results:
                form_entries.append(("photo_ids", result["id"]))

            encoded = urlencode(form_entries)
            response = await client.post(
                "/api/prints",
                content=encoded,
                headers={"HX-Request": "true", "Content-Type": "application/x-www-form-urlencoded"},
            )
        finally:
            await mock_client.aclose()
            print_order_service._http_client = None

        assert response.status_code == 202, response.text
        html = response.text
        assert "Order submitted successfully" in html
        assert "Reference:" in html
        assert captured_payloads, "Expected Prodigi payload to be captured"
        assert captured_payloads[0]["items"][0]["copies"] == 1
        assert captured_headers and captured_headers[0] == "example-key"


@pytest.mark.asyncio
async def test_post_prints_form_prodigi_error_returns_partial_with_ok_status(tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    _create_image(bright_path, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        scan_id, results = await _complete_scan(client, tmp_path)
        assert results, "Expected shortlist results"
        target_photo = results[0]
        toggle_response = await client.post(
            f"/api/scans/{scan_id}/photos/{target_photo['id']}/selection",
            data={"selected": "true"},
            headers={"HX-Request": "true"},
        )
        assert toggle_response.status_code == 200

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502, json={"message": "Prodigi is unavailable"})

        mock_client = httpx.AsyncClient(transport=MockTransport(handler), base_url="https://api.sandbox.prodigi.com/v4.0")
        print_order_service._http_client = mock_client

        try:
            form_entries: list[tuple[str, str]] = [
                ("scan_id", scan_id),
                ("photo_ids", target_photo["id"]),
                ("name", "Grace Hopper"),
                ("email", "grace@example.com"),
                ("line1", "2 Example Road"),
                ("line2", ""),
                ("city", "New York"),
                ("state", "NY"),
                ("postal_code", "10001"),
                ("country_code", "US"),
                ("shipping_method", "STANDARD"),
                ("copies", "1"),
                ("asset_base_url", "https://assets.example.com"),
                ("api_key", "example-key"),
            ]
            encoded = urlencode(form_entries)
            response = await client.post(
                "/api/prints",
                content=encoded,
                headers={"HX-Request": "true", "Content-Type": "application/x-www-form-urlencoded"},
            )
        finally:
            await mock_client.aclose()
            print_order_service._http_client = None

        assert response.status_code == 200
        assert "Unable to submit print order" in response.text
        assert "Prodigi is unavailable" in response.text
        assert "Prodigi debug details" in response.text
        assert '"status_code": 502' in response.text
        assert '"shippingMethod": "Standard"' in response.text


@pytest.mark.asyncio
async def test_print_order_submission_falls_back_when_httpx_typeerror(monkeypatch, tmp_path) -> None:
    bright_path = tmp_path / "bright.jpg"
    _create_image(bright_path, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        scan_id, results = await _complete_scan(client, tmp_path)
        assert results, "Expected shortlist results"
        target_photo = results[0]
        toggle_response = await client.post(
            f"/api/scans/{scan_id}/photos/{target_photo['id']}/selection",
            data={"selected": "true"},
            headers={"HX-Request": "true"},
        )
        assert toggle_response.status_code == 200

        class BrokenAsyncClient:
            def __init__(self, *args, **kwargs):
                raise TypeError("int() argument must be a string, a bytes-like object or a real number, not 'dict'")

        async def fake_stdlib(self, *, payload, headers):
            class DummyResponse:
                def __init__(self) -> None:
                    self.status_code = 202

                def json(self) -> dict[str, object]:
                    return {"id": "PO-FALLBACK", "status": "submitted"}

                @property
                def text(self) -> str:
                    return json.dumps(self.json())

            return DummyResponse()

        monkeypatch.setattr(print_orders.httpx, "AsyncClient", BrokenAsyncClient)
        monkeypatch.setattr(print_orders.PrintOrderService, "_post_with_stdlib", fake_stdlib, raising=False)

        form_entries = [
            ("scan_id", scan_id),
            ("photo_ids", target_photo["id"]),
            ("name", "Grace Hopper"),
            ("email", "grace@example.com"),
            ("line1", "2 Example Road"),
            ("line2", ""),
            ("city", "New York"),
            ("state", "NY"),
            ("postal_code", "10001"),
            ("country_code", "US"),
            ("shipping_method", "STANDARD"),
            ("copies", "1"),
            ("asset_base_url", "https://assets.example.com"),
            ("api_key", "example-key"),
        ]
        encoded = urlencode(form_entries)
        response = await client.post(
            "/api/prints",
            content=encoded,
            headers={"HX-Request": "true", "Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 202
        assert "Order submitted successfully" in response.text
        assert "PO-FALLBACK" in response.text

@pytest.mark.asyncio
async def test_print_controls_fragment_requires_scan_id(tmp_path) -> None:
    primary = tmp_path / "primary.jpg"
    secondary = tmp_path / "secondary.jpg"
    _create_image(primary, (255, 255, 255), datetime(2024, 1, 10, tzinfo=timezone.utc))
    _create_image(secondary, (125, 125, 125), datetime(2024, 1, 11, tzinfo=timezone.utc))

    os.environ["PHOTO_ARCHIVIST_THUMBNAIL_DIR"] = str(tmp_path / "thumbs")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        scan_id, results = await _complete_scan(client, tmp_path)
        toggle_response = await client.post(
            f"/api/scans/{scan_id}/photos/{results[0]['id']}/selection",
            data={"selected": "true"},
            headers={"HX-Request": "true"},
        )
        assert toggle_response.status_code == 200

        fragment_without_id = await client.get("/fragments/print")
        assert fragment_without_id.status_code == 200
        assert "Run a scan before sending selected photos to print." in fragment_without_id.text

        fragment_with_id = await client.get(f"/fragments/print?scan_id={scan_id}")
        assert fragment_with_id.status_code == 200
        html = fragment_with_id.text
        assert 'name="asset_base_url"' in html
        assert "Submit print order" in html
        assert "document.getElementById('print-controls')?.dataset?.scanId" in html
