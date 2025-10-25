from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import (
    PhotoItem,
    Run,
    RunStatus,
    ShortlistEntry,
    ShortlistEntry as ShortlistEntryModel,
)


@dataclass
class RunTotals:
    total_items: int
    eligible_items: int
    shortlisted_items: int


@dataclass
class ShortlistProjection:
    photo: PhotoItem
    entry: ShortlistEntry


class Repository:
    """Lightweight data-access helpers for scan-related persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # Run helpers -----------------------------------------------------------------

    def latest_completed_run(self) -> Optional[Run]:
        stmt = (
            select(Run)
            .where(Run.status == RunStatus.COMPLETED.value)
            .order_by(Run.finished_at.desc())  # type: ignore[arg-type]
        )
        return self.session.execute(stmt).scalars().first()

    def latest_completed_run_for_month(self, month: str) -> Optional[Run]:
        stmt = (
            select(Run)
            .where(Run.status == RunStatus.COMPLETED.value, Run.month == month)
            .order_by(Run.finished_at.desc())  # type: ignore[arg-type]
        )
        return self.session.execute(stmt).scalars().first()

    def create_run(self, *, month: str, name: Optional[str] = None) -> Run:
        run = Run(
            name=name,
            month=month,
            status=RunStatus.PENDING.value,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        self.session.flush()
        return run

    def mark_run_running(self, run: Run) -> None:
        run.status = RunStatus.RUNNING.value
        run.started_at = datetime.now(timezone.utc)
        self.session.add(run)
        self.session.flush()

    def mark_run_completed(
        self,
        run: Run,
        *,
        delta_cursor: str,
        totals: RunTotals,
    ) -> None:
        run.status = RunStatus.COMPLETED.value
        run.delta_cursor = delta_cursor
        run.finished_at = datetime.now(timezone.utc)
        run.total_items = totals.total_items
        run.eligible_items = totals.eligible_items
        run.shortlisted_items = totals.shortlisted_items
        self.session.add(run)
        self.session.flush()

    def mark_run_failed(self, run: Run, error: str) -> None:
        run.status = RunStatus.FAILED.value
        run.error_message = error
        run.finished_at = datetime.now(timezone.utc)
        self.session.add(run)
        self.session.flush()

    # Photo helpers ---------------------------------------------------------------

    def upsert_photo(
        self,
        *,
        drive_item_id: str,
        drive_id: str,
        filename: str,
        download_url: Optional[str],
        captured_at: Optional[datetime],
        width: Optional[int],
        height: Optional[int],
        month: Optional[str],
        quality_score: Optional[float],
        eligible: bool,
    ) -> PhotoItem:
        stmt = select(PhotoItem).where(PhotoItem.drive_item_id == drive_item_id)
        photo = self.session.execute(stmt).scalar_one_or_none()
        if photo is None:
            photo = PhotoItem(
                drive_item_id=drive_item_id,
                drive_id=drive_id,
                filename=filename,
                download_url=download_url,
                captured_at=captured_at,
                width=width,
                height=height,
                month=month,
                quality_score=quality_score,
                eligible=eligible,
            )
            self.session.add(photo)
        else:
            photo.drive_id = drive_id
            photo.filename = filename
            photo.download_url = download_url
            photo.captured_at = captured_at
            photo.width = width
            photo.height = height
            photo.month = month
            photo.quality_score = quality_score
            photo.eligible = eligible

        self.session.flush()
        return photo

    # Shortlist helpers -----------------------------------------------------------

    def replace_shortlist(
        self,
        *,
        run: Run,
        ranked_photo_ids: Iterable[Tuple[int, float]],
    ) -> None:
        delete_stmt = delete(ShortlistEntryModel).where(
            ShortlistEntryModel.run_id == run.id
        )
        self.session.execute(delete_stmt)

        for index, (photo_id, score) in enumerate(ranked_photo_ids, start=1):
            entry = ShortlistEntry(
                run_id=run.id,
                photo_id=photo_id,
                rank=index,
                score=score,
            )
            self.session.add(entry)
        self.session.flush()

    def shortlist_for_month(self, month: str) -> List[ShortlistProjection]:
        run = self.latest_completed_run_for_month(month)
        if run is None:
            return []

        stmt = (
            select(ShortlistEntry, PhotoItem)
            .join(PhotoItem, PhotoItem.id == ShortlistEntry.photo_id)
            .where(ShortlistEntry.run_id == run.id)
            .order_by(ShortlistEntry.rank.asc(), ShortlistEntry.id.asc())
        )
        rows = self.session.execute(stmt).all()
        return [
            ShortlistProjection(photo=photo, entry=entry) for entry, photo in rows
        ]
