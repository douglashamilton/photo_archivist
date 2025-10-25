from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger("photo_archivist.graph.client")


GraphTokenSupplier = Callable[[], str]


@dataclass
class DriveItem:
    """Subset of Microsoft Graph driveItem fields needed for scanning."""

    id: str
    drive_id: str
    name: str
    mime_type: str
    download_url: Optional[str]
    captured_at: Optional[datetime]
    width: Optional[int]
    height: Optional[int]
    last_modified: Optional[datetime]


class GraphClient:
    """Lightweight Microsoft Graph wrapper for delta queries."""

    def __init__(
        self,
        token_supplier: GraphTokenSupplier,
        *,
        root_path: str,
        page_size: int,
        base_url: str = "https://graph.microsoft.com/v1.0",
        session: Optional[requests.Session] = None,
    ) -> None:
        if page_size <= 0:
            raise ValueError("page_size must be positive")

        self._token_supplier = token_supplier
        self._base_url = base_url.rstrip("/")
        normalized = root_path.strip() or "/me/drive/root"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        self._root_path = normalized.rstrip("/")
        self._page_size = page_size
        self._session = session or requests.Session()

    # Public API -------------------------------------------------------------

    def get_delta(self, cursor: Optional[str] = None) -> Tuple[List[DriveItem], str]:
        """Fetch driveItem changes using the delta API."""
        request_url = self._cursor_to_url(cursor)
        params: Optional[Dict[str, str]] = None
        if cursor is None:
            params = {"$top": str(self._page_size)}

        collected: List[DriveItem] = []
        delta_link: Optional[str] = None
        next_url: Optional[str] = request_url
        next_params: Optional[Dict[str, str]] = params

        while next_url:
            logger.debug(
                {"event": "graph.delta.request", "url": next_url, "params": next_params}
            )
            response = self._session.get(
                next_url,
                headers=self._auth_headers(),
                params=next_params,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            raw_items = payload.get("value", [])
            for raw in raw_items:
                item = self._parse_drive_item(raw)
                if item is not None:
                    collected.append(item)

            next_link = payload.get("@odata.nextLink")
            if next_link:
                next_url = next_link
                next_params = None  # Server provides full query string.
            else:
                next_url = None

            delta_candidate = payload.get("@odata.deltaLink")
            if delta_candidate:
                delta_link = delta_candidate

        if not delta_link:
            logger.error({"event": "graph.delta.missing_delta_link"})
            raise RuntimeError("graph.delta_missing")

        return collected, delta_link

    # Internal helpers ------------------------------------------------------

    def _auth_headers(self) -> Dict[str, str]:
        token = self._token_supplier()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _cursor_to_url(self, cursor: Optional[str]) -> str:
        if cursor:
            return cursor if cursor.startswith("http") else f"{self._base_url}{cursor}"
        return f"{self._base_url}{self._root_path}/delta"

    @staticmethod
    def _parse_drive_item(raw: Dict[str, object]) -> Optional[DriveItem]:
        file_info = _coerce_dict(raw.get("file"))
        if not file_info:
            return None

        mime_type = str(file_info.get("mimeType") or "")
        if mime_type.lower() != "image/jpeg":
            return None

        parent_reference = _coerce_dict(raw.get("parentReference"))
        drive_id = str(parent_reference.get("driveId") or "")
        download_url = raw.get("@microsoft.graph.downloadUrl")
        captured_at = _parse_datetime(
            _coerce_dict(raw.get("photo")).get("takenDateTime")
        )
        dimensions = _coerce_dict(raw.get("photo"))
        if not dimensions:
            dimensions = _coerce_dict(raw.get("image"))

        width = _parse_int(dimensions.get("width") if dimensions else None)
        height = _parse_int(dimensions.get("height") if dimensions else None)

        return DriveItem(
            id=str(raw.get("id") or ""),
            drive_id=drive_id,
            name=str(raw.get("name") or ""),
            mime_type=mime_type,
            download_url=str(download_url) if download_url is not None else None,
            captured_at=captured_at,
            width=width,
            height=height,
            last_modified=_parse_datetime(raw.get("lastModifiedDateTime")),
        )


def _coerce_dict(value: object) -> Dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _parse_datetime(value: object) -> Optional[datetime]:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        logger.debug({"event": "graph.delta.invalid_datetime", "value": value})
        return None


def _parse_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.debug({"event": "graph.delta.invalid_int", "value": value})
        return None
