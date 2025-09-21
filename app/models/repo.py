"""Database repository layer."""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
import sqlmodel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .domain import (
    User, AuthToken, SyncState, Asset, Score,
    Shortlist, ShortlistItem, PrintOrder, PrintOrderItem,
    PrintOrderStatus
)


class Repository:
    """Repository for database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    # User operations
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        """Create new user."""
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    # Auth token operations
    async def upsert_auth_token(self, token: AuthToken) -> AuthToken:
        """Update or insert auth token."""
        existing = await self._session.execute(
            select(AuthToken).where(AuthToken.user_id == token.user_id)
        )
        db_token = existing.scalar_one_or_none()
        
        if db_token:
            db_token.access_token = token.access_token
            db_token.refresh_token = token.refresh_token
            db_token.expires_at = token.expires_at
        else:
            self._session.add(token)
        
        await self._session.commit()
        return db_token or token

    # Sync state operations
    async def get_sync_state(self, user_id: UUID) -> Optional[SyncState]:
        """Get sync state for user."""
        result = await self._session.execute(
            select(SyncState).where(SyncState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_sync_state(self, state: SyncState) -> SyncState:
        """Update sync state."""
        self._session.add(state)
        await self._session.commit()
        await self._session.refresh(state)
        return state

    # Asset operations
    async def upsert_asset(self, asset: Asset) -> Asset:
        """Update or insert asset."""
        existing = await self._session.execute(
            select(Asset).where(Asset.item_id == asset.item_id)
        )
        db_asset = existing.scalar_one_or_none()
        
        if db_asset:
            for field, value in asset.dict().items():
                setattr(db_asset, field, value)
        else:
            self._session.add(asset)
        
        await self._session.commit()
        return db_asset or asset

    async def get_assets_by_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> Tuple[List[Asset], int]:
        """Get paginated assets for user."""
        # Get total count
        count_query = select(sqlmodel.func.count()).select_from(Asset).where(Asset.user_id == user_id)
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        # Get paginated results
        query = select(Asset).where(Asset.user_id == user_id)
        
        result = await self._session.execute(
            query.offset(offset).limit(limit)
        )
        assets = list(result.scalars().all())
        
        return assets, total

    # Score operations
    async def upsert_score(self, score: Score) -> Score:
        """Update or insert score."""
        query = select(Score).where(Score.asset_item_id == score.asset_item_id)
        existing = await self._session.execute(query)
        db_score = existing.scalar_one_or_none()
        
        if db_score:
            for field, value in score.dict().items():
                setattr(db_score, field, value)
        else:
            self._session.add(score)
        
        await self._session.commit()
        return db_score or score

    # Shortlist operations
    async def create_shortlist(self, shortlist: Shortlist) -> Shortlist:
        """Create new shortlist."""
        self._session.add(shortlist)
        await self._session.commit()
        await self._session.refresh(shortlist)
        return shortlist

    async def get_latest_shortlist(self, user_id: UUID) -> Optional[Shortlist]:
        """Get user's latest shortlist."""
        query = select(Shortlist).where(Shortlist.user_id == user_id)
        result = await self._session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def update_shortlist_selection(
        self, shortlist_id: UUID, item_id: str, selected: bool
    ) -> bool:
        """Update selection status of shortlist item."""
        shortlist = await self._session.execute(
            select(Shortlist).where(Shortlist.id == shortlist_id)
        )
        db_shortlist = shortlist.scalar_one_or_none()
        
        if not db_shortlist:
            return False
            
        for item in db_shortlist.items:
            if item.asset_item_id == item_id:
                item.selected = selected
                break
        
        await self._session.commit()
        return True

    # Print order operations
    async def create_print_order(self, order: PrintOrder) -> PrintOrder:
        """Create new print order."""
        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)
        return order

    async def get_print_order(self, order_id: UUID) -> Optional[PrintOrder]:
        """Get print order by ID."""
        result = await self._session.execute(
            select(PrintOrder).where(PrintOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def update_print_order_status(
        self, order_id: UUID, provider_order_id: str, status: PrintOrderStatus
    ) -> bool:
        """Update print order status."""
        order = await self.get_print_order(order_id)
        if not order:
            return False
            
        order.provider_order_id = provider_order_id
        order.status = status
        
        await self._session.commit()
        return True