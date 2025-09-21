"""Sync API routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.schemas import SyncRunRequest, SyncRunResponse
from ..models.domain import SyncState
from ..models.repo import Repository
from ..utils.errors import AppError, with_retry
from ..sync.delta_scanner import DeltaScanner
from ..db import get_session
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/sync")


@router.post("/run", response_model=SyncRunResponse)
async def trigger_sync(
    request: SyncRunRequest,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user),
    scanner: DeltaScanner = Depends(DeltaScanner),
) -> SyncRunResponse:
    """Trigger a manual sync run."""
    repo = Repository(session)
    
    try:
        state = await repo.get_sync_state(user.id)
        delta_link = state.delta_link if state else None
        
        # Run sync with retries on throttling
        async def run_sync():
            return await scanner.scan(user.id, delta_link)
            
        new_delta_link = await with_retry(run_sync)
        
        # Update sync state
        new_state = SyncState(
            user_id=user.id,
            delta_link=new_delta_link,
            last_run_at=datetime.utcnow(),
            last_status="success"
        )
        await repo.update_sync_state(new_state)
        
        return SyncRunResponse(
            started_at=new_state.last_run_at,
            delta_link_set=bool(new_delta_link)
        )
        
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.__class__.__name__, "detail": str(e)}
        )