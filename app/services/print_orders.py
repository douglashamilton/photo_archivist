from __future__ import annotations

import os
from typing import Iterable
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

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class PrintOrderService:
    """Coordinate print order submissions to Prodigi."""

    def __init__(
        self,
        scan_manager: ScanManager,
        *,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
    ) -> None:
        self._scan_manager = scan_manager
        self._http_client = http_client
        self._base_url = base_url or os.getenv("PHOTO_ARCHIVIST_PRODIGI_BASE_URL", "https://api.sandbox.prodigi.com/v4.0")
        self._default_asset_base = os.getenv("PHOTO_ARCHIVIST_ASSET_BASE_URL")
        self._default_api_key = os.getenv("PHOTO_ARCHIVIST_PRODIGI_API_KEY")

    async def submit_print_order(self, request: PrintOrderRequest) -> PrintOrderSubmission:
        outcome = self._scan_manager.get_outcome(request.scan_id)
        if outcome is None:
            raise UnknownScanError("Scan not found or expired.")

        photo_map = {photo.id: photo for photo in outcome.results}
        selected_photos: list[PhotoResult] = []
        for photo_id in request.photo_ids:
            photo = photo_map.get(photo_id)
            if photo is None:
                raise NoSelectedPhotosError(f"Photo {photo_id} is no longer available in the shortlist.")
            selected_photos.append(photo)

        if not selected_photos:
            raise NoSelectedPhotosError("Select at least one photo to print.")

        asset_base_url = request.asset_base_url or self._default_asset_base
        if not asset_base_url:
            raise PrintOrderConfigurationError(
                "Asset base URL is required. Set PHOTO_ARCHIVIST_ASSET_BASE_URL or supply one in the request."
            )

        api_key = request.api_key or self._default_api_key
        if not api_key:
            raise PrintOrderConfigurationError(
                "Prodigi API key is required. Set PHOTO_ARCHIVIST_PRODIGI_API_KEY or include one in the request."
            )

        payload = self._build_payload(
            request=request,
            photos=selected_photos,
            asset_base_url=asset_base_url,
        )

        submission = await self._send_to_prodigi(payload=payload, api_key=api_key)
        return submission

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
                "sku": "GLOBAL-PRINT-4X6",
                "copies": request.copies,
                "itemReference": str(photo.id),
                "attributes": {},
                "assets": [
                    {
                        "assetType": "image",
                        "assetUrl": asset_url,
                        "assetReference": str(photo.id),
                    }
                ],
            }
            items.append(item)

        recipient = request.recipient
        payload: dict[str, object] = {
            "shippingMethod": request.shipping_method,
            "recipient": {
                "name": recipient.name,
                "email": recipient.email,
                "address": {
                    "line1": recipient.address.line1,
                    "line2": recipient.address.line2,
                    "city": recipient.address.city,
                    "state": recipient.address.state,
                    "postalOrZipCode": recipient.address.postal_code,
                    "countryCode": recipient.address.country_code,
                },
            },
            "items": items,
            "metadata": {"scanId": str(request.scan_id)},
        }
        return payload

    async def _send_to_prodigi(self, *, payload: dict[str, object], api_key: str) -> PrintOrderSubmission:
        headers = {
            "X-Prodigi-Api-Key": api_key,
            "Content-Type": "application/json",
        }

        client = self._http_client
        if client is not None:
            response = await client.post("/orders", json=payload, headers=headers)
        else:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=30.0) as http_client:
                response = await http_client.post("/orders", json=payload, headers=headers)

        if response.status_code >= 400:
            detail = ""
            try:
                body = response.json()
                detail = body.get("message") or body.get("error") or str(body)
            except ValueError:
                detail = response.text
            raise ProdigiAPIError(response.status_code, detail or "Prodigi rejected the order.")

        try:
            data = response.json()
        except ValueError as exc:  # pragma: no cover - unexpected response
            raise ProdigiAPIError(response.status_code, "Prodigi response did not include JSON.") from exc

        order_id = (
            data.get("id")
            or data.get("orderId")
            or (data.get("order") or {}).get("id")
            or (data.get("order") or {}).get("reference")
        )
        status = data.get("status") or "submitted"

        if not order_id:
            raise ProdigiAPIError(response.status_code, "Prodigi response did not include an order reference.")

        return PrintOrderSubmission(order_id=str(order_id), status=status, raw_response=data)


def _compose_asset_url(base_url: str, scan_id: UUID, photo: PhotoResult) -> str:
    filename = quote(photo.path.name)
    return f"{base_url}/{scan_id}/{photo.id}/{filename}"
