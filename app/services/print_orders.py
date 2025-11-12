from __future__ import annotations

import asyncio
import json
import os
import ssl
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import quote
from uuid import UUID

import httpx

from app.models import PhotoResult, PrintOrderRequest, PrintOrderSubmission
from app.services.scan_manager import ScanManager


class PrintOrderError(Exception):
    """Base error for print order submission issues."""


class UnknownScanError(PrintOrderError):
    """Raised when the referenced scan cannot be found."""


class NoSelectedPhotosError(PrintOrderError):
    """Raised when no photos are available for printing."""


class PrintOrderConfigurationError(PrintOrderError):
    """Raised when configuration such as API key or asset host is missing."""


class ProdigiAPIError(PrintOrderError):
    """Raised when the Prodigi API returns an error response."""

    def __init__(self, status_code: int, message: str, *, debug: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.debug = debug
        super().__init__(message)


@dataclass(slots=True)
class _SimpleResponse:
    status_code: int
    body: bytes

    def json(self) -> object:
        if not self.body:
            return {}
        return json.loads(self.body.decode("utf-8"))

    @property
    def text(self) -> str:
        if not self.body:
            return ""
        return self.body.decode("utf-8", errors="replace")


class PrintOrderService:
    """Coordinate print order submissions to Prodigi."""

    def __init__(
        self,
        scan_manager: ScanManager,
        *,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        default_asset_base: str | None = None,
        default_api_key: str | None = None,
    ) -> None:
        self._scan_manager = scan_manager
        self._http_client = http_client
        self._base_url = base_url or os.getenv("PHOTO_ARCHIVIST_PRODIGI_BASE_URL", "https://api.sandbox.prodigi.com/v4.0")
        self._default_asset_base = default_asset_base or os.getenv("PHOTO_ARCHIVIST_ASSET_BASE_URL")
        self._default_api_key = default_api_key or os.getenv("PHOTO_ARCHIVIST_PRODIGI_API_KEY")
        self._timeout = 30.0

    async def submit_print_order(self, request: PrintOrderRequest) -> PrintOrderSubmission:
        outcome = self._scan_manager.get_outcome(request.scan_id)
        if outcome is None:
            raise UnknownScanError("Scan not found or expired.")

        photo_map = {photo.id: photo for photo in outcome.results}
        selected_photos: list[PhotoResult] = []
        for photo_id in request.photo_ids:
            photo = photo_map.get(photo_id)
            if photo is None:
                raise NoSelectedPhotosError(
                    f"Photo {photo_id} is no longer available in the shortlist."
                )
            selected_photos.append(photo)

        if not selected_photos:
            raise NoSelectedPhotosError("Select at least one photo to print.")

        asset_base_url = self._resolve_asset_base_url(request.asset_base_url)
        if not asset_base_url:
            raise PrintOrderConfigurationError(
                "Asset base URL is required. Set PHOTO_ARCHIVIST_ASSET_BASE_URL "
                "or supply one in the request."
            )

        api_key = self._resolve_api_key()
        if not api_key:
            raise PrintOrderConfigurationError(
                "Prodigi API key is required. Set PHOTO_ARCHIVIST_PRODIGI_API_KEY in the server environment."
            )

        payload = self._build_payload(
            request=request,
            photos=selected_photos,
            asset_base_url=asset_base_url,
        )

        submission = await self._send_to_prodigi(payload=payload, api_key=api_key)
        return submission

    def _resolve_asset_base_url(self, explicit: str | None) -> str | None:
        if explicit:
            cleaned = explicit.strip()
            if cleaned:
                return cleaned
        env_value = os.getenv("PHOTO_ARCHIVIST_ASSET_BASE_URL")
        candidate = env_value or self._default_asset_base
        if not candidate:
            return None
        cleaned = candidate.strip()
        return cleaned or None

    def _resolve_api_key(self) -> str | None:
        env_value = os.getenv("PHOTO_ARCHIVIST_PRODIGI_API_KEY")
        candidate = env_value or self._default_api_key
        if not candidate:
            return None
        cleaned = candidate.strip()
        return cleaned or None

    def _build_payload(
        self,
        *,
        request: PrintOrderRequest,
        photos: Iterable[PhotoResult],
        asset_base_url: str,
    ) -> dict[str, object]:
        base = asset_base_url.rstrip("/")
        items = []
        for photo in photos:
            asset_url = _compose_asset_url(base, request.scan_id, photo)
            item = {
                "sku": "GLOBAL-PAP-4X6",
                "copies": request.copies,
                "merchantReference": str(photo.id),
                "attributes": {},
                "sizing": "fillPrintArea",
                "assets": [
                    {
                        "printArea": "default",
                        "url": asset_url,
                    }
                ],
            }
            items.append(item)

        recipient = request.recipient
        payload: dict[str, object] = {
            "shippingMethod": _prodigi_shipping_method(request.shipping_method),
            "recipient": {
                "name": recipient.name,
                "email": recipient.email,
                "address": {
                    "line1": recipient.address.line1,
                    "line2": recipient.address.line2,
                    "townOrCity": recipient.address.city,
                    "stateOrCounty": recipient.address.state,
                    "postalOrZipCode": recipient.address.postal_code,
                    "countryCode": recipient.address.country_code,
                },
            },
            "items": items,
            "metadata": {"scanId": str(request.scan_id)},
        }
        return payload

    async def _send_to_prodigi(
        self, *, payload: dict[str, object], api_key: str
    ) -> PrintOrderSubmission:
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

        response = await self._post_payload(payload=payload, headers=headers)

        if response.status_code >= 400:
            parsed_body: object | None = None
            try:
                parsed_body = response.json()
            except ValueError:
                parsed_body = None

            if parsed_body is not None:
                detail = self._format_prodigi_error(parsed_body)
            else:
                detail = response.text

            debug = self._build_debug_details(
                payload=payload,
                response=response,
                response_json=parsed_body,
                response_text=response.text,
            )
            raise ProdigiAPIError(
                response.status_code,
                detail or "Prodigi rejected the order.",
                debug=debug,
            )

        try:
            data = response.json()
            if not isinstance(data, dict):
                debug = self._build_debug_details(
                    payload=payload,
                    response=response,
                    response_json=data,
                    response_text=response.text,
                )
                raise ProdigiAPIError(
                    response.status_code,
                    "Unexpected response format from Prodigi.",
                    debug=debug,
                )
        except ValueError as exc:  # pragma: no cover - unexpected response
            debug = self._build_debug_details(
                payload=payload,
                response=response,
                response_text=response.text,
            )
            raise ProdigiAPIError(
                response.status_code, "Prodigi response did not include JSON.", debug=debug
            ) from exc

        order_id = (
            data.get("id")
            or data.get("orderId")
            or (data.get("order") or {}).get("id")
            or (data.get("order") or {}).get("reference")
        )
        status = data.get("status") or "submitted"

        if not order_id:
            debug = self._build_debug_details(
                payload=payload,
                response=response,
                response_json=data,
                response_text=response.text,
            )
            raise ProdigiAPIError(
                response.status_code,
                "Prodigi response did not include an order reference.",
                debug=debug,
            )

        return PrintOrderSubmission(order_id=str(order_id), status=status, raw_response=data)

    async def _post_payload(self, *, payload: dict[str, object], headers: dict[str, str]):
        if self._http_client is not None:
            return await self._http_client.post("/orders", json=payload, headers=headers)

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout
            ) as http_client:
                return await http_client.post("/orders", json=payload, headers=headers)
        except TypeError as exc:
            if "int() argument must be a string" not in str(exc):
                raise
            return await self._post_with_stdlib(payload=payload, headers=headers)

    async def _post_with_stdlib(
        self, *, payload: dict[str, object], headers: dict[str, str]
    ) -> _SimpleResponse:
        return await asyncio.to_thread(self._post_with_stdlib_sync, payload, headers)

    def _post_with_stdlib_sync(
        self, payload: dict[str, object], headers: dict[str, str]
    ) -> _SimpleResponse:
        data = json.dumps(payload).encode("utf-8")
        url = f"{self._base_url.rstrip('/')}/orders"
        request = urllib_request.Request(url, data=data, method="POST")
        for key, value in headers.items():
            request.add_header(key, value)

        context = ssl.create_default_context()
        try:
            with urllib_request.urlopen(
                request, context=context, timeout=self._timeout
            ) as response:
                body = response.read()
                status_code = response.getcode()
        except urllib_error.HTTPError as exc:
            body = exc.read()
            status_code = exc.code
        except urllib_error.URLError as exc:
            debug = self._build_debug_details(
                payload=payload,
                response=None,
                error=str(exc.reason),
                response_text="",
            )
            raise ProdigiAPIError(0, f"Unable to reach Prodigi: {exc.reason}", debug=debug) from exc
        except TimeoutError as exc:  # pragma: no cover - safety net
            debug = self._build_debug_details(
                payload=payload,
                response=None,
                error="timeout",
                response_text="",
            )
            raise ProdigiAPIError(0, "Prodigi request timed out.", debug=debug) from exc
        return _SimpleResponse(status_code=status_code, body=body)

    def _format_prodigi_error(self, payload: object) -> str:
        if isinstance(payload, dict):
            message = payload.get("message") or payload.get("error")
            outcome = payload.get("Outcome") or payload.get("outcome")
            if outcome and not message:
                message = f"Prodigi reported '{outcome}'."
                trace = payload.get("TraceParent") or payload.get("traceparent")
                if trace:
                    message = f"{message} Trace: {trace}."
            if message:
                return message
            return json.dumps(payload, ensure_ascii=False)
        return str(payload)

    def _build_debug_details(
        self,
        *,
        payload: dict[str, object],
        response: httpx.Response | _SimpleResponse | None,
        response_json: object | None = None,
        response_text: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        debug_response: dict[str, Any] = {}
        if response is not None:
            debug_response["status_code"] = response.status_code
        if response_json is not None:
            debug_response["json"] = response_json
        if response_text is not None:
            debug_response["body"] = response_text
        elif response is not None:
            debug_response["body"] = response.text
        if error:
            debug_response["error"] = error
        return {"request": payload, "response": debug_response}


def _compose_asset_url(base_url: str, scan_id: UUID, photo: PhotoResult) -> str:
    filename = quote(photo.path.name)
    return f"{base_url}/{scan_id}/{photo.id}/{filename}"


def _prodigi_shipping_method(method: str) -> str:
    mapping = {
        "BUDGET": "Budget",
        "STANDARD": "Standard",
        "STANDARDPLUS": "StandardPlus",
        "STANDARD_PLUS": "StandardPlus",
        "EXPRESS": "Express",
        "OVERNIGHT": "Overnight",
    }
    normalized = method.strip().upper()
    return mapping.get(normalized, method)
