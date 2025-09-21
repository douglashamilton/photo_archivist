"""FastAPI dependency providers."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from .models.repo import Repository


async def get_db_session(app) -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    session = AsyncSession(app.state.engine)
    try:
        yield session
    finally:
        await session.close()


async def get_repository(
    session: AsyncSession = Depends(get_db_session)
) -> Repository:
    """Get repository dependency."""
    return Repository(session)