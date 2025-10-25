from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable, Iterator, List, Optional, Sequence, Tuple

import pytest
from photo_archivist.graph import DriveItem
from photo_archivist.services.scan_service import RunSummary, ScanService
from photo_archivist.storage.models import Base, Run, RunStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _build_session_factory() -> Callable[[], Iterator[Session]]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    @contextmanager
    def session_scope() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return session_scope


class _FakeGraphClient:
    def __init__(self) -> None:
        self.calls: List[Optional[str]] = []
        self.items: Sequence[DriveItem] = []
        self.delta_cursor: str = "delta-0"

    def get_delta(
        self, cursor: Optional[str] = None
    ) -> Tuple[Sequence[DriveItem], str]:
        self.calls.append(cursor)
        return self.items, self.delta_cursor


class _BoomGraphClient:
    def get_delta(
        self, cursor: Optional[str] = None
    ) -> Tuple[Sequence[DriveItem], str]:
        raise RuntimeError("graph.down")


def _drive_item(
    *,
    id_suffix: str,
    captured_at: datetime,
    width: int,
    height: int,
) -> DriveItem:
    return DriveItem(
        id=f"item-{id_suffix}",
        drive_id="drive-123",
        name=f"{captured_at.date()}_{id_suffix}.jpg",
        mime_type="image/jpeg",
        download_url=f"https://example/{id_suffix}",
        captured_at=captured_at,
        width=width,
        height=height,
        last_modified=captured_at,
    )


def test_scan_service_filters_and_shortlists() -> None:
    session_factory = _build_session_factory()
    graph = _FakeGraphClient()
    service = ScanService(
        graph_client=graph,
        shortlist_size=10,
        session_factory=session_factory,
    )

    target_month = "2025-08"

    eligible_item = _drive_item(
        id_suffix="eligible",
        captured_at=datetime(2025, 8, 2, 10, tzinfo=timezone.utc),
        width=4032,
        height=3024,
    )
    low_res_item = _drive_item(
        id_suffix="lowres",
        captured_at=datetime(2025, 8, 5, 14, tzinfo=timezone.utc),
        width=800,
        height=600,
    )
    other_month_item = _drive_item(
        id_suffix="othermonth",
        captured_at=datetime(2025, 7, 28, 9, tzinfo=timezone.utc),
        width=4032,
        height=3024,
    )

    graph.items = [eligible_item, low_res_item, other_month_item]
    graph.delta_cursor = "delta-1"

    summary = service.run(month=target_month)

    assert isinstance(summary, RunSummary)
    assert summary.month == target_month
    assert summary.total_items == 3
    assert summary.eligible_items == 1
    assert summary.shortlisted_items == 1
    assert summary.delta_cursor == "delta-1"
    assert graph.calls == [None]

    shortlist = service.shortlist_for_month(target_month)
    assert len(shortlist) == 1
    assert shortlist[0].drive_item_id == eligible_item.id
    assert shortlist[0].rank == 1


def test_scan_service_uses_previous_delta_cursor() -> None:
    session_factory = _build_session_factory()
    graph = _FakeGraphClient()
    service = ScanService(
        graph_client=graph,
        shortlist_size=5,
        session_factory=session_factory,
    )

    graph.items = [
        _drive_item(
            id_suffix="first",
            captured_at=datetime(2025, 8, 11, 9, tzinfo=timezone.utc),
            width=4000,
            height=3000,
        )
    ]
    graph.delta_cursor = "delta-first"
    service.run(month="2025-08")

    graph.items = [
        _drive_item(
            id_suffix="second",
            captured_at=datetime(2025, 9, 2, 11, tzinfo=timezone.utc),
            width=4100,
            height=3000,
        )
    ]
    graph.delta_cursor = "delta-second"
    service.run(month="2025-09")

    # Expect first call to use None, second call to use previous cursor.
    assert graph.calls == [None, "delta-first"]


def test_scan_service_marks_run_failed_on_exception() -> None:
    session_factory = _build_session_factory()
    service = ScanService(
        graph_client=_BoomGraphClient(),
        shortlist_size=5,
        session_factory=session_factory,
    )

    with pytest.raises(RuntimeError):
        service.run(month="2025-08")

    # Verify a failed run was recorded.
    with session_factory() as session:
        run: Run = session.query(Run).order_by(Run.id.desc()).first()  # type: ignore[assignment]
        assert run is not None
        assert run.status == RunStatus.FAILED.value
        assert run.error_message == "graph.down"
