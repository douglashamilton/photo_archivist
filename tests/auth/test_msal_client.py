from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest


class _FakePublicClientApplication:
    """Minimal stand-in for msal.PublicClientApplication."""

    def __init__(self) -> None:
        self.acquire_device_flow_token_called = False
        self.acquire_pkce_token_called = False
        self.cached_accounts: list[Dict[str, Any]] = []
        self.token_result: Dict[str, Any] | None = {
            "access_token": "fake-access",
            "refresh_token": "fake-refresh",
            "expires_in": 3600,
        }

    def get_accounts(self) -> list[Dict[str, Any]]:
        return self.cached_accounts

    def acquire_token_by_device_flow(
        self,
        device_flow: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.acquire_device_flow_token_called = True
        if device_flow.get("error"):
            raise RuntimeError("device flow error")
        return self.token_result or {}

    def initiate_device_flow(self, scopes: list[str]) -> Dict[str, Any]:
        return {"user_code": "1234", "message": "Go to device login", "scopes": scopes}

    def acquire_token_interactive(
        self,
        scopes: list[str],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        self.acquire_pkce_token_called = True
        return self.token_result or {}


class _FakeCrypto:
    """Fake Fernet helper to capture encryption/decryption behavior."""

    def __init__(self) -> None:
        self.encrypt_calls: list[bytes] = []
        self.decrypt_calls: list[bytes] = []
        self.tokens: list[bytes] = []

    def encrypt_bytes(
        self,
        data: bytes,
        *,
        key_name: str = "default",
        service_name: str = "photo_archivist",
    ) -> bytes:
        self.encrypt_calls.append(data)
        token = b"enc:" + data
        self.tokens.append(token)
        return token

    def decrypt_bytes(
        self,
        token: bytes,
        *,
        key_name: str = "default",
        service_name: str = "photo_archivist",
    ) -> bytes:
        self.decrypt_calls.append(token)
        if not token.startswith(b"enc:"):
            raise ValueError("invalid encrypted payload")
        return token[len(b"enc:") :]


@pytest.fixture
def tmp_cache(tmp_path: Path) -> Path:
    return tmp_path / "msal_cache.json"


@pytest.fixture
def fake_pca() -> _FakePublicClientApplication:
    return _FakePublicClientApplication()


@pytest.fixture
def fake_crypto() -> _FakeCrypto:
    return _FakeCrypto()


def test_msal_client_encrypts_and_decrypts_cache(
    tmp_cache: Path,
    fake_pca: _FakePublicClientApplication,
    fake_crypto: _FakeCrypto,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the MSAL client writes encrypted cache data and can read it back."""
    from photo_archivist.auth import msal_client as msal_mod

    monkeypatch.setattr(
        msal_mod.msal, "PublicClientApplication", lambda *args, **kwargs: fake_pca
    )
    monkeypatch.setattr(
        msal_mod.crypto, "encrypt_bytes", fake_crypto.encrypt_bytes, raising=False
    )
    monkeypatch.setattr(
        msal_mod.crypto, "decrypt_bytes", fake_crypto.decrypt_bytes, raising=False
    )
    monkeypatch.setattr(msal_mod.settings, "AUTH_CACHE_PATH", tmp_cache, raising=False)

    client = msal_mod.MSALClient()
    client._persist_cache(b"{}")

    assert tmp_cache.exists()
    on_disk = tmp_cache.read_bytes()
    assert on_disk.startswith(b"enc:")
    assert fake_crypto.encrypt_calls == [b"{}"]

    round_trip = client._load_cache()
    assert round_trip == b"{}"
    assert fake_crypto.decrypt_calls == [on_disk]


def test_msal_client_uses_cached_accounts(
    tmp_cache: Path,
    fake_pca: _FakePublicClientApplication,
    fake_crypto: _FakeCrypto,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When an account is already cached, ensure_connected short-circuits."""
    from photo_archivist.auth import msal_client as msal_mod

    fake_pca.cached_accounts = [{"home_account_id": "abc"}]

    monkeypatch.setattr(
        msal_mod.msal, "PublicClientApplication", lambda *args, **kwargs: fake_pca
    )
    monkeypatch.setattr(
        msal_mod.crypto, "encrypt_bytes", fake_crypto.encrypt_bytes, raising=False
    )
    monkeypatch.setattr(
        msal_mod.crypto, "decrypt_bytes", fake_crypto.decrypt_bytes, raising=False
    )
    monkeypatch.setattr(msal_mod.settings, "AUTH_CACHE_PATH", tmp_cache, raising=False)

    client = msal_mod.MSALClient()
    status = client.ensure_connected(flow="device_code")

    assert status["status"] == "already_connected"
    assert not fake_pca.acquire_device_flow_token_called
    assert not fake_pca.acquire_pkce_token_called
