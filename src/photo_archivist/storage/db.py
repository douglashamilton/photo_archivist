from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger("photo_archivist.storage")

# Module-level engine and session factory cache
_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def _make_sqlite_url(path: Union[str, Path]) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    # Use forward slashes for SQLAlchemy URL on Windows
    return f"sqlite:///{p.as_posix()}"


def get_engine(path: Optional[Union[str, Path]] = None) -> Engine:
    """Return a SQLAlchemy Engine for the given path.

    - If path is None or 'memory', return an in-memory SQLite engine.
    - If path is a filesystem path, ensure parent directories exist and return a file-based SQLite engine.
    """
    global _engine, _SessionFactory

    if path is None or path == "memory":
        url = "sqlite:///:memory:"
    else:
        # allow passing Path or string file path
        url = _make_sqlite_url(path)
        # ensure parent dir exists
        try:
            p = Path(path)
            parent = p.parent
            if str(path) and parent and not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # best-effort; do not fail creation for odd inputs
            logger.debug("Could not ensure parent dir for %s", path, exc_info=True)

    _engine = sa.create_engine(url, echo=False, future=True)
    _SessionFactory = sessionmaker(bind=_engine, future=True)
    return _engine


def init_db(engine: Optional[Engine] = None) -> None:
    """Create database schema for the application's models.

    If engine is not provided, an in-memory engine will be used.
    """
    global _engine, _SessionFactory

    if engine is None:
        engine = get_engine(None)

    # create tables from metadata
    Base.metadata.create_all(engine)

    # cache engine and session factory
    _engine = engine
    _SessionFactory = sessionmaker(bind=_engine, future=True)

    # Log storage initialization without leaking sensitive details
    try:
        url = engine.url
    except Exception:
        url = "<unknown>"
    logger.info("storage.init_db completed; engine=%s", url)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy Session using the cached engine/session factory.

    The session is rolled back on exception and closed on exit.
    """
    global _SessionFactory, _engine
    if _SessionFactory is None:
        # lazily create an in-memory engine if none configured
        get_engine(None)

    assert _SessionFactory is not None
    sess: Session = _SessionFactory()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()
