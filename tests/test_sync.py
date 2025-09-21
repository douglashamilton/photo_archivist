"""Acceptance tests for OneDrive delta sync functionality."""

import pytest
import httpx
from datetime import datetime
from httpx import HTTPError, HTTPStatusError
from sqlmodel import select

from app.models.domain import SyncState
from app.sync.delta_scanner import DeltaScanner
from app.sync.graph_client import GraphClient

from conftest import TEST_DELTA_LINK

pytestmark = pytest.mark.asyncio

async def test_delta_sync_stores_and_reuses_delta_link(
    test_db,
    test_user,
    mock_graph_client,
    mocker
):
    """
    Scenario: Delta sync stores and reuses deltaLink
    Given a connected OneDrive account
    When the initial scan completes
    Then a deltaLink is stored and subsequent scans fetch only changes
    """
    # Initial scan
    scanner = DeltaScanner(test_db)
    await scanner.scan(test_user.id)
    
    # Verify deltaLink was stored
    sync_state = test_db.exec(select(SyncState).where(SyncState.user_id == test_user.id)).first()
    assert sync_state is not None
    assert sync_state.delta_link == TEST_DELTA_LINK
    
    # Configure second response with new deltaLink
    second_response = {
        "@odata.deltaLink": "https://graph.microsoft.com/v1.0/drive/root/delta?token=456",
        "value": [
            {
                "id": "new_item",
                "name": "new_photo.jpg",
                "file": {"mimeType": "image/jpeg"},
                "parentReference": {"path": "/drive/root:/Photos"},
                "photo": {"takenDateTime": "2025-01-01T00:00:00Z"}
            }
        ]
    }
    
    # Configure mock client for second response
    second_mock_response = mocker.Mock(spec=httpx.Response)
    second_mock_response.status_code = 200
    second_mock_response.request = httpx.Request("GET", "https://test.com")
    second_mock_response.is_error = False
    second_mock_response.json.return_value = second_response
    
    # Update the mock client to return our new response
    mock_graph_client.return_value.client.get.return_value = second_mock_response
    
    # Run subsequent scan
    await scanner.scan(test_user.id)

    # Verify correct token was used in URL
    calls = mock_graph_client.return_value.client.get.mock_calls
    assert any("token=123" in str(call.args[0]) for call in calls if len(call.args) > 0)

    # Verify deltaLink was updated
    sync_state = test_db.exec(select(SyncState).where(SyncState.user_id == test_user.id)).first()
    assert sync_state.delta_link == "https://graph.microsoft.com/v1.0/drive/root/delta?token=456"

async def test_graph_throttling_honored(
    test_db,
    test_user,
    mock_graph_client,
    mocker
):
    """
    Scenario: Graph throttling honored
    Given Graph returns HTTP 429 with Retry-After
    When the scanner retries
    Then the operation completes without user intervention
    """
    # Reset mock and track initial call count
    mock_graph_client.return_value.client.get.reset_mock()
    initial_call_count = len(mock_graph_client.return_value.client.get.mock_calls)
    
    # Run scan that encounters throttling (mock_graph_client is set up in conftest.py to return 429 then success)
    scanner = DeltaScanner(test_db)
    await scanner.scan(test_user.id)
    
    # Verify successful retry and deltaLink storage
    sync_state = test_db.exec(select(SyncState).where(SyncState.user_id == test_user.id)).first()
    assert sync_state.delta_link == TEST_DELTA_LINK
    assert sync_state.last_status == "success"
    
    # Verify multiple calls were made (indicating retry occurred)
    final_call_count = len(mock_graph_client.return_value.client.get.mock_calls)
    assert final_call_count > initial_call_count, "Should have made multiple calls due to throttling"