from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from photo_archivist.app import app
from photo_archivist.config import settings


class _StubMSALClient:
    """Test double to observe how the auth connect endpoint drives MSAL."""

    def __init__(self, cache_path: Path, expected_flow: str = "device_code") -> None:
        self.cache_path = cache_path
        self.expected_flow = expected_flow
        self.calls: List[str] = []
        self.cache_writes: List[bytes] = []
        self.raise_for_flow: Dict[str, Exception] = {}

    def ensure_connected(self, flow: str) -> Dict[str, Any]:
        self.calls.append(flow)
        if flow in self.raise_for_flow:
            raise self.raise_for_flow[flow]
        if flow != self.expected_flow:
            raise AssertionError(f"Unexpected flow: {flow!r}")
        payload = b"encrypted-token-payload"
        self.cache_path.write_bytes(payload)
        self.cache_writes.append(payload)
        return {"status": "connected", "flow": flow, "new_connection": True}

    def cached_status(self) -> Dict[str, Any]:
        """Simulate a call that reports whether a cached account already exists."""
        return {"status": "already_connected", "flow": self.expected_flow}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def token_cache_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cache_path = tmp_path / "msal_cache.bin"
    monkeypatch.setattr(settings, "AUTH_CACHE_PATH", cache_path, raising=False)
    return cache_path


def test_auth_connect_device_flow_encrypts_cache_and_returns_connected(
    client: TestClient,
    token_cache_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_client = _StubMSALClient(
        cache_path=token_cache_path,
        expected_flow="device_code",
    )

    # Provide the endpoint with our stubbed MSAL client factory.
    monkeypatch.setattr(
        "photo_archivist.app.get_msal_client",
        lambda: stub_client,
        raising=False,
    )

    response = client.post("/api/auth/connect", json={"flow": "device_code"})
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "connected"
    assert stub_client.calls == ["device_code"]
    assert token_cache_path.exists()
    assert token_cache_path.read_bytes() == b"encrypted-token-payload"


def test_auth_connect_rejects_unknown_flow(client: TestClient) -> None:
    response = client.post("/api/auth/connect", json={"flow": "totally_invalid"})
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "unsupported_flow"
