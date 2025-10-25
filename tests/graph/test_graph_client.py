from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest
import responses
from photo_archivist.graph import GraphClient
from responses import matchers


def _token_supplier_factory(tokens: List[str]) -> str:
    tokens.append("called")
    return "fake-token"


@responses.activate
def test_get_delta_combines_pages_and_filters_non_jpeg() -> None:
    token_calls: List[str] = []

    client = GraphClient(
        lambda: _token_supplier_factory(token_calls),
        root_path="/me/drive/root",
        page_size=2,
    )

    first_url = "https://graph.microsoft.com/v1.0/me/drive/root/delta"
    responses.add(
        responses.GET,
        first_url,
        match=[matchers.query_param_matcher({"$top": "2"})],
        json={
            "value": [
                {
                    "id": "photo-1",
                    "name": "2025-08-01.jpg",
                    "parentReference": {"driveId": "drive-123"},
                    "file": {"mimeType": "image/jpeg"},
                    "@microsoft.graph.downloadUrl": "https://onedrive.test/photo-1",
                    "lastModifiedDateTime": "2025-08-02T10:00:00Z",
                    "photo": {
                        "takenDateTime": "2025-08-01T09:30:00Z",
                        "width": 4032,
                        "height": 3024,
                    },
                },
                {
                    "id": "doc-1",
                    "name": "notes.docx",
                    "parentReference": {"driveId": "drive-123"},
                    "file": {
                        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    },
                },
            ],
            "@odata.nextLink": f"{first_url}?$skiptoken=abc",
        },
        status=200,
    )

    responses.add(
        responses.GET,
        f"{first_url}?$skiptoken=abc",
        json={
            "value": [
                {
                    "id": "photo-2",
                    "name": "2025-08-03.jpg",
                    "parentReference": {"driveId": "drive-123"},
                    "file": {"mimeType": "image/jpeg"},
                    "@microsoft.graph.downloadUrl": "https://onedrive.test/photo-2",
                    "lastModifiedDateTime": "2025-08-03T12:15:00+00:00",
                    "photo": {
                        "takenDateTime": "2025-08-03T12:00:00+00:00",
                        "width": 3000,
                        "height": 2000,
                    },
                }
            ],
            "@odata.deltaLink": f"{first_url}?$deltatoken=xyz",
        },
        status=200,
    )

    items, cursor = client.get_delta()

    assert len(items) == 2
    assert cursor == f"{first_url}?$deltatoken=xyz"

    first_item = items[0]
    assert first_item.id == "photo-1"
    assert first_item.mime_type == "image/jpeg"
    assert first_item.captured_at == datetime(2025, 8, 1, 9, 30, tzinfo=timezone.utc)
    assert first_item.width == 4032
    assert first_item.height == 3024

    second_item = items[1]
    assert second_item.id == "photo-2"

    assert responses.calls[0].request.headers["Authorization"] == "Bearer fake-token"
    assert len(token_calls) >= 1


@responses.activate
def test_get_delta_uses_existing_cursor_without_top_parameter() -> None:
    token_calls: List[str] = []
    client = GraphClient(
        lambda: _token_supplier_factory(token_calls),
        root_path="/me/drive/root",
        page_size=5,
    )

    cursor = "https://graph.microsoft.com/v1.0/me/drive/root/delta?$deltatoken=prev"
    responses.add(
        responses.GET,
        cursor,
        json={
            "value": [],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/drive/root/delta?$deltatoken=new",
        },
        status=200,
    )

    items, new_cursor = client.get_delta(cursor=cursor)

    assert items == []
    assert (
        new_cursor
        == "https://graph.microsoft.com/v1.0/me/drive/root/delta?$deltatoken=new"
    )
    assert responses.calls[0].request.url == cursor
    assert "$top" not in responses.calls[0].request.url
    assert len(token_calls) == 1


@responses.activate
def test_get_delta_raises_when_delta_link_missing() -> None:
    client = GraphClient(
        lambda: "fake-token",
        root_path="/me/drive/root",
        page_size=10,
    )

    responses.add(
        responses.GET,
        "https://graph.microsoft.com/v1.0/me/drive/root/delta",
        match=[matchers.query_param_matcher({"$top": "10"})],
        json={"value": []},
        status=200,
    )

    with pytest.raises(RuntimeError) as excinfo:
        client.get_delta()

    assert "graph.delta_missing" in str(excinfo.value)
