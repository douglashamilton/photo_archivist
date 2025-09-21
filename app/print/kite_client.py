"""Kite print service API client."""
from typing import Dict, Optional
import httpx
from httpx import HTTPStatusError, Response
from sqlmodel import Session

from ..models.domain import PrintOrder, PrintMode, PrintOrderStatus
from ..config import settings


class KiteError(Exception):
    """Kite API error."""
    pass


class KiteClient:
    """Client for Kite.ly print API."""
    
    BASE_URL = "https://api.kite.ly/v4.0"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key."""
        self.api_key = api_key or settings.kite_api_key
    
    async def create_order(
        self,
        order: PrintOrder,
        db: Optional[Session] = None
    ) -> Dict[str, str]:
        """
        Create test print order.
        
        Args:
            order: Order details
            db: Optional SQLModel session for updating order status
            
        Returns:
            Dict with order_id and status
            
        Raises:
            ValueError: If live mode attempted or no photos selected
            KiteError: For API errors
        """
        if order.mode != PrintMode.TEST:
            raise ValueError("Only test mode orders are supported")
            
        if not order.items:
            raise ValueError("No photos selected for printing")
        
        # Build order payload
        payload = {
            "test": True,
            "reference": str(order.id),
            "currency": "GBP",
            "items": [
                {
                    "sku": order.sku.value,
                    "copies": item.qty,
                    "assets": [{
                        "url": f"https://graph.microsoft.com/v1.0/drive/items/{item.asset_item_id}/thumbnails/0/large/content"
                    }],
                    "shipping": {
                        "address": {
                            "line1": "Test Address",
                            "city": "London",
                            "postcode": "SW1A 1AA",
                            "country": "GB"
                        }
                    }
                }
                for item in order.items
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/orders",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Update order status
                provider_id = result.get("order_id", result.get("id"))  # Handle both response formats
                order.provider_order_id = provider_id
                order.status = PrintOrderStatus.SUBMITTED

                # Update order in db if session provided
                if db:
                    db.add(order)

                return {
                    "order_id": provider_id,
                    "status": "submitted"  # Status from Kite API
                }
                
        except (HTTPStatusError, httpx.HTTPError) as e:
            # Handle API errors with proper response
            try:
                if isinstance(e, HTTPStatusError):
                    response = e.response
                    error_detail = response.json().get("error", {}).get("message", str(e))
                    raise KiteError(f"Kite API error: {error_detail}")
            except (ValueError, AttributeError):
                pass
            raise KiteError(f"Kite API error: {str(e)}")

    async def get_order_status(
        self,
        provider_order_id: str
    ) -> Optional[PrintOrderStatus]:
        """
        Check test order status.
        
        Args:
            provider_order_id: Kite order ID
            
        Returns:
            Optional[PrintOrderStatus]: Current order status if found
            
        Raises:
            KiteError: For API errors
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/orders/{provider_order_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                if response.status_code == 404:
                    return None
                    
                response.raise_for_status()
                result = response.json()
                
                # Map Kite status to our enum
                status_map = {
                    "draft": PrintOrderStatus.QUEUED,
                    "created": PrintOrderStatus.QUEUED,
                    "submitted": PrintOrderStatus.SUBMITTED,
                    "cancelled": PrintOrderStatus.FAILED,
                    "failed": PrintOrderStatus.FAILED
                }
                
                return status_map.get(
                    result["status"],
                    PrintOrderStatus.QUEUED  # Default for test mode
                )
                
        except (HTTPStatusError, httpx.HTTPError) as e:
            # Handle API errors with proper response
            try:
                if isinstance(e, HTTPStatusError):
                    response = e.response
                    error_detail = response.json().get("error", {}).get("message", str(e))
                    raise KiteError(f"Kite API error: {error_detail}")
            except (ValueError, AttributeError):
                pass
            raise KiteError(f"Kite API error: {str(e)}")

    @staticmethod
    async def handle_api_error(response: httpx.Response) -> None:
        """
        Handle Kite API error responses.
        
        Args:
            response: Error response from API
            
        Raises:
            KiteError with error details
        """
        try:
            error = response.json().get("error", {})
            message = error.get("message", "Unknown error")
            code = error.get("code", "unknown")
            raise KiteError(f"Kite API error ({code}): {message}")
        except ValueError:
            raise KiteError(f"Kite API error: {response.text}")