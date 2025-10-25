from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient

from photo_archivist.app import app
from photo_archivist.services.scan_service import RunSummary, ShortlistItem


class _StubScanService:
    def __init__(self) -> None:
        self.run_calls: List[Tuple[Optional[str], Optional[int]]] = []
        self.shortlist_months: List[str] = []
        self.run_response = RunSummary(
            run_id=1,
            month="2025-08",
            total_items=3,
            eligible_items=2,
            shortlisted_items=2,
            delta_cursor="cursor-1",
        )
        self.shortlist_items: List[ShortlistItem] = [
            ShortlistItem(
                drive_item_id="item-1",
                filename="2025-08-01.jpg",
                captured_at=datetime(2025, 8, 1, 9, tzinfo=timezone.utc),
                width=4032,
                height=3024,
                quality_score=12_192_768.0,
                download_url="https://example/item-1",
                rank=1,
            ),
            ShortlistItem(
                drive_item_id="item-2",
                filename="2025-08-05.jpg",
                captured_at=datetime(2025, 8, 5, 12, tzinfo=timezone.utc),
                width=3000,
                height=2000,
                quality_score=6_000_000.0,
                download_url="https://example/item-2",
                rank=2,
            ),
        ]
        self.raise_runtime: Optional[str] = None
        self.shortlist_empty = False

    def run(self, *, month: Optional[str] = None, limit: Optional[int] = None) -> RunSummary:
        if self.raise_runtime:
            raise RuntimeError(self.raise_runtime)
        self.run_calls.append((month, limit))
        return self.run_response

    def shortlist_for_month(self, month: str):
        if self.shortlist_empty:
            return []
        self.shortlist_months.append(month)
        return self.shortlist_items


@pytest.fixture
def client_and_stub(monkeypatch: pytest.MonkeyPatch) -> Tuple[TestClient, _StubScanService]:
    stub = _StubScanService()
    monkeypatch.setattr("photo_archivist.app._get_scan_service", lambda: stub)
    client = TestClient(app)
    return client, stub


def test_trigger_scan_returns_summary(client_and_stub: Tuple[TestClient, _StubScanService]) -> None:
    client, stub = client_and_stub
    response = client.post(
        "/api/run/scan",
        json={"month": "2025-08", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == 1
    assert data["month"] == "2025-08"
    assert data["eligible_items"] == 2
    assert stub.run_calls == [("2025-08", 5)]


def test_trigger_scan_surfaces_auth_conflict(client_and_stub: Tuple[TestClient, _StubScanService]) -> None:
    client, stub = client_and_stub
    stub.raise_runtime = "auth.not_connected"
    response = client.post("/api/run/scan", json={"month": "2025-08"})
    assert response.status_code == 409
    assert response.json()["detail"] == "auth.not_connected"


def test_get_shortlist_returns_items(client_and_stub: Tuple[TestClient, _StubScanService]) -> None:
    client, stub = client_and_stub
    response = client.get("/api/shortlist", params={"month": "2025-08"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["month"] == "2025-08"
    assert len(payload["items"]) == 2
    assert payload["items"][0]["drive_item_id"] == "item-1"
    assert stub.shortlist_months == ["2025-08"]


def test_get_shortlist_returns_404_when_missing(client_and_stub: Tuple[TestClient, _StubScanService]) -> None:
    client, stub = client_and_stub
    stub.shortlist_empty = True
    response = client.get("/api/shortlist", params={"month": "2025-08"})
    assert response.status_code == 404
    assert response.json()["detail"] == "shortlist_not_found"
