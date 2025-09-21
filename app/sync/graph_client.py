"""Microsoft Graph API client for photo operations."""
from typing import Dict, Any, Optional, AsyncGenerator
import json
from datetime import datetime
import httpx
from httpx import HTTPStatusError
from ..config import settings


class GraphClient:
    """Microsoft Graph client for photo sync."""
    
    def __init__(self, access_token: str):
        """Initialize with access token."""
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient()

    async def get_photo_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve photo metadata from Graph API.
        
        Args:
            file_id: OneDrive item ID
            
        Returns:
            Dict with photo metadata
            
        Raises:
            HTTPError: For API errors
        """
        url = f"{self.base_url}/me/drive/items/{file_id}"
        async with self.client as client:
            response = await client.get(url, headers=self.headers)
            await self._handle_error_response(response)
            return response.json()

    async def get_photo_content(self, file_id: str) -> bytes:
        """
        Download photo binary content.
        
        Args:
            file_id: OneDrive item ID
            
        Returns:
            Photo bytes
            
        Raises:
            HTTPError: For API errors
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/content"
        async with self.client as client:
            response = await client.get(url, headers=self.headers)
            await self._handle_error_response(response)
            return response.content

    async def get_thumbnail(self, file_id: str, size: str = "large") -> Optional[bytes]:
        """
        Get photo thumbnail in specified size.
        
        Args:
            file_id: OneDrive item ID
            size: Thumbnail size (small, medium, large)
            
        Returns:
            Thumbnail bytes or None if not available
            
        Raises:
            HTTPError: For API errors
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/thumbnails/0/{size}"
        async with self.client as client:
            try:
                response = await client.get(url, headers=self.headers)
                await self._handle_error_response(response)
                return response.content
            except httpx.HTTPError:
                return None  # Thumbnails may not exist for all files

    async def list_delta(
        self,
        delta_token: Optional[str] = None,
        page_size: int = 200
    ) -> Dict[str, Any]:
        """
        List changes using delta query.
        
        Args:
            delta_token: Optional token from previous sync
            page_size: Number of items per page
            
        Returns:
            Dict with changes and next delta link
        """
        params = {
            "$select": "id,name,file,photo,size,parentReference",
            "$top": page_size
        }
        
        # Use delta_token if provided, otherwise start fresh
        if delta_token:
            # If full URL provided, use it, otherwise construct URL with token
            if delta_token.startswith("http"):
                url = delta_token
            else:
                url = f"{self.base_url}/me/drive/root/delta?token={delta_token}"
        else:
            url = f"{self.base_url}/me/drive/root/delta"
        
        result = {
            "value": [],
            "@odata.deltaLink": None
        }
        
        async with self.client as client:
            while url:
                while True:
                    response = await client.get(
                        url if delta_token else url,
                        params=None if delta_token else params,
                        headers=self.headers
                    )
                    try:
                        await self._handle_error_response(response)
                        break  # If no exception, break out of retry loop
                    except HTTPStatusError as e:
                        # Re-raise if not 429 or if 429 handled by _handle_error_response
                        if e.response.status_code != 429:
                            raise
                data = response.json()
                
                # Append results
                result["value"].extend(data.get("value", []))
                
                # Get next link or delta link
                url = data.get("@odata.nextLink")
                if not url:
                    result["@odata.deltaLink"] = data.get("@odata.deltaLink")
                    break
                
                delta_token = None  # Clear token after first request
                
        return result

    async def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error responses from Graph API.
        
        Args:
            response: HTTPX response object
            
        Raises:
            HTTPStatusError: With error details from Graph API
        """
        if response.is_error:
            # Check for 429 Too Many Requests
            if response.status_code == 429 and "Retry-After" in response.headers:
                retry_after = int(response.headers["Retry-After"])
                from asyncio import sleep
                await sleep(retry_after)  # Honor throttling delay
                return  # Let caller retry the request
                
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown Graph API error")
            raise HTTPStatusError(
                message=error_msg,
                request=response.request,
                response=response
            )