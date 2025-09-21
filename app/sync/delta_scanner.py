"""Delta-based photo sync with Microsoft Graph API."""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from uuid import UUID

from sqlmodel import Session, select

from ..models.domain import User, Asset, SyncState, AuthToken
from .graph_client import GraphClient


class DeltaScanner:
    """Photo scanner using Microsoft Graph delta queries."""
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    async def _get_delta_link(self, user_id: UUID) -> Optional[str]:
        """Get stored delta link for user."""
        sync_state = self.db.exec(
            select(SyncState).where(SyncState.user_id == user_id)
        ).first()
        return sync_state.delta_link if sync_state else None

    async def _store_delta_link(self, user_id: UUID, delta_link: str) -> None:
        """Store new delta link for user."""
        sync_state = self.db.exec(
            select(SyncState).where(SyncState.user_id == user_id)
        ).first()
        
        now = datetime.now(UTC)
        
        if sync_state:
            sync_state.delta_link = delta_link
            sync_state.last_run_at = now
            sync_state.last_status = "success"
            sync_state.updated_at = now
        else:
            sync_state = SyncState(
                user_id=user_id,
                delta_link=delta_link,
                last_run_at=now,
                last_status="success",
                created_at=now,
                updated_at=now
            )
            self.db.add(sync_state)
            
        self.db.commit()

    def _is_valid_photo(self, item: Dict[str, Any]) -> bool:
        """Check if item is a valid photo."""
        if not item.get("file"):
            return False
        
        mime = item["file"].get("mimeType", "")
        if not mime.startswith("image/"):
            return False
            
        parent_path = item.get("parentReference", {}).get("path", "")
        return "/Photos" in parent_path

    async def scan(self, user_id: UUID) -> List[Asset]:
        """
        Scan for photo changes using delta query.
        
        Args:
            user_id: User to scan photos for
            
        Returns:
            List of new or updated photo assets
            
        Raises:
            HTTPError: For API errors
            ValueError: For auth/config errors
        """
        # Get user and token
        user = self.db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise ValueError("User not found")
            
        auth_token = self.db.exec(
            select(AuthToken).where(AuthToken.user_id == user_id)
        ).first()
        if not auth_token or auth_token.expires_at < datetime.now(UTC).replace(tzinfo=None):
            raise ValueError("No valid access token")
            
        # Init Graph client
        client = GraphClient(auth_token.access_token)
        
        # Get stored delta link
        delta_link = await self._get_delta_link(user_id)
        
        # Get changes from Graph API
        changes = await client.list_delta(            delta_token=delta_link.split("token=")[-1] if delta_link else None)
        
        # Process changes
        new_assets = []
        for item in changes.get("value", []):
            # Skip non-photo files
            if not self._is_valid_photo(item):
                continue
                
            # Get or create asset
            asset = self.db.exec(
                select(Asset).where(Asset.item_id == item["id"])
            ).first()
            
            taken_at = None
            if "photo" in item and "takenDateTime" in item["photo"]:
                taken_at = datetime.fromisoformat(
                    item["photo"]["takenDateTime"].replace("Z", "+00:00")
                )
            
            # Update or create asset
            if asset:
                asset.last_seen = datetime.now(UTC)
                asset.taken_at = taken_at or asset.taken_at
            else:
                asset = Asset(
                    item_id=item["id"],
                    user_id=user_id,
                    path=item["parentReference"]["path"],
                    mime=item["file"]["mimeType"],
                    taken_at=taken_at or datetime.now(UTC),
                    width=item.get("photo", {}).get("width", 0),
                    height=item.get("photo", {}).get("height", 0),
                    last_seen=datetime.now(UTC)
                )
                new_assets.append(asset)
                
            self.db.add(asset)
            
        # Store new delta link
        if "@odata.deltaLink" in changes:
            await self._store_delta_link(user_id, changes["@odata.deltaLink"])
            
        self.db.commit()
        return new_assets

async def handle_backoff(response: httpx.Response) -> None:
    """Implement exponential backoff for API rate limits."""
    raise NotImplementedError()


async def validate_photo_type(item: Dict[str, Any]) -> bool:
    """Check if item is a supported photo type."""
    raise NotImplementedError()