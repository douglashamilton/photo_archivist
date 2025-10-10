from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import msal
from msal import SerializableTokenCache
from photo_archivist.config import settings
from photo_archivist.utils import crypto

logger = logging.getLogger("photo_archivist.auth.msal")


CACHE_KEY_NAME = "msal_token_cache"


def _cache_path() -> Path:
    return Path(settings.AUTH_CACHE_PATH)


class MSALClient:
    """Thin wrapper around msal.PublicClientApplication with encrypted token caching."""

    def __init__(self) -> None:
        self.cache = SerializableTokenCache()
        self._load_cache()

        self.app = msal.PublicClientApplication(
            client_id=settings.MSAL_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{settings.MSAL_TENANT_ID}",
            token_cache=self.cache,
        )

    # Internal cache helpers -------------------------------------------------

    def _persist_cache(self, raw_cache: bytes) -> None:
        logger.debug({"event": "auth.cache.persist"})
        encrypted = crypto.encrypt_bytes(raw_cache, key_name=CACHE_KEY_NAME)
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encrypted)

    def _load_cache(self) -> Optional[bytes]:
        path = _cache_path()
        if not path.exists():
            return None
        try:
            encrypted = path.read_bytes()
            decrypted: bytes = crypto.decrypt_bytes(encrypted, key_name=CACHE_KEY_NAME)
            self.cache.deserialize(decrypted.decode("utf-8"))
            logger.debug({"event": "auth.cache.loaded"})
            return decrypted
        except Exception:  # pragma: no cover - failures bubble up in tests
            logger.exception({"event": "auth.cache.load_failed"})
            return None

    def _save_cache_if_changed(self) -> None:
        if self.cache.has_state_changed:
            serialized = self.cache.serialize().encode("utf-8")
            self._persist_cache(serialized)
            logger.info({"event": "auth.cache.saved"})

    # Public API -------------------------------------------------------------

    def ensure_connected(self, flow: str = "pkce") -> Dict[str, Any]:
        """Ensure tokens exist. Supports 'pkce' and 'device_code' flows."""
        existing_accounts = self.app.get_accounts()
        if existing_accounts:
            account_count = len(existing_accounts)
            logger.info({"event": "auth.connect.cached", "accounts": account_count})
            return {"status": "already_connected", "accounts": account_count}

        if flow == "device_code":
            result = self._run_device_code_flow()
        elif flow == "pkce":
            result = self._run_pkce_flow()
        else:
            logger.warning({"event": "auth.connect.unsupported_flow", "flow": flow})
            raise ValueError("unsupported_flow")

        self._save_cache_if_changed()
        return {"status": "connected", "flow": flow, "result": result}

    # Flow implementations ---------------------------------------------------

    def _run_device_code_flow(self) -> Dict[str, Any]:
        logger.info({"event": "auth.connect.device_code.start"})
        device_flow = self.app.initiate_device_flow(scopes=settings.MSAL_SCOPES)
        if "user_code" not in device_flow:
            message = device_flow.get(
                "error_description", "Device code initiation failed"
            )
            logger.error(
                {"event": "auth.connect.device_code.error", "message": message}
            )
            raise RuntimeError(message)

        logger.info(
            {
                "event": "auth.connect.device_code.prompt",
                "message": device_flow.get("message"),
            }
        )
        result = self.app.acquire_token_by_device_flow(device_flow)
        self._validate_result(result)
        logger.info({"event": "auth.connect.device_code.success"})
        return self._sanitize_result(result, include_account=True)

    def _run_pkce_flow(self) -> Dict[str, Any]:
        logger.info({"event": "auth.connect.pkce.start"})
        result = self.app.acquire_token_interactive(
            scopes=settings.MSAL_SCOPES,
            prompt="select_account",
            timeout=600,
        )
        self._validate_result(result)
        logger.info({"event": "auth.connect.pkce.success"})
        return self._sanitize_result(result, include_account=True)

    @staticmethod
    def _validate_result(result: Dict[str, Any]) -> None:
        if not result or "access_token" not in result:
            message = (
                result.get("error_description")
                if isinstance(result, dict)
                else "Unknown error"
            )
            logger.error({"event": "auth.connect.token_failure", "message": message})
            raise RuntimeError(message)

    @staticmethod
    def _sanitize_result(
        result: Dict[str, Any], *, include_account: bool = False
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"expires_in": result.get("expires_in")}
        if include_account:
            account = result.get("accounts") or result.get("client_info")
            payload["account_hint"] = account
        return payload


_MSAL_SINGLETON: Optional[MSALClient] = None


def get_msal_client() -> MSALClient:
    global _MSAL_SINGLETON
    if _MSAL_SINGLETON is None:
        _MSAL_SINGLETON = MSALClient()
    return _MSAL_SINGLETON
