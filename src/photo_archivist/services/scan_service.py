from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable, ContextManager, List, Optional, Sequence, Tuple

from photo_archivist.graph import DriveItem, GraphClient
from photo_archivist.storage.repo import Repository, RunTotals
from sqlalchemy.orm import Session

logger = logging.getLogger("photo_archivist.services.scan")


SessionFactory = Callable[[], ContextManager[Session]]


@dataclass
class RunSummary:
    run_id: int
    month: str
    total_items: int
    eligible_items: int
    shortlisted_items: int
    delta_cursor: str


@dataclass
class ShortlistItem:
    drive_item_id: str
    filename: Optional[str]
    captured_at: Optional[datetime]
    width: Optional[int]
    height: Optional[int]
    quality_score: Optional[float]
    download_url: Optional[str]
    rank: Optional[int]


class ScanService:
    """Coordinates Microsoft Graph scanning with persistence and ranking."""

    def __init__(
        self,
        *,
        graph_client: GraphClient,
        shortlist_size: int,
        session_factory: SessionFactory,
    ) -> None:
        if shortlist_size <= 0:
            raise ValueError("shortlist_size must be positive")

        self._graph_client = graph_client
        self._shortlist_size = shortlist_size
        self._session_factory = session_factory

    # Public API -----------------------------------------------------------------

    def run(
        self, *, month: Optional[str] = None, limit: Optional[int] = None
    ) -> RunSummary:
        month_bucket = month or _previous_month_string()
        if not _is_valid_month(month_bucket):
            raise ValueError("invalid_month")

        shortlist_limit = limit or self._shortlist_size
        if shortlist_limit <= 0:
            raise ValueError("invalid_shortlist_limit")

        with self._session_factory() as session:
            repo = Repository(session)
            run = repo.create_run(month=month_bucket, name="manual_scan")
            repo.mark_run_running(run)

            previous_run = repo.latest_completed_run()
            cursor = (
                previous_run.delta_cursor
                if previous_run and previous_run.delta_cursor
                else None
            )

            logger.info(
                {
                    "event": "scan.started",
                    "month": month_bucket,
                    "run_id": run.id,
                    "cursor": bool(cursor),
                }
            )

            try:
                items, delta_cursor = self._graph_client.get_delta(cursor=cursor)
                stats, shortlist = self._process_items(
                    session=session,
                    repo=repo,
                    items=items,
                    month_bucket=month_bucket,
                    shortlist_limit=shortlist_limit,
                )
                repo.replace_shortlist(run=run, ranked_photo_ids=shortlist)
                repo.mark_run_completed(run, delta_cursor=delta_cursor, totals=stats)
                session.commit()
                logger.info(
                    {
                        "event": "scan.completed",
                        "run_id": run.id,
                        "month": month_bucket,
                        "totals": stats.__dict__,
                    }
                )
                return RunSummary(
                    run_id=run.id,
                    month=month_bucket,
                    total_items=stats.total_items,
                    eligible_items=stats.eligible_items,
                    shortlisted_items=stats.shortlisted_items,
                    delta_cursor=delta_cursor,
                )
            except Exception as exc:
                repo.mark_run_failed(run, error=str(exc))
                session.commit()
                logger.exception({"event": "scan.failed", "run_id": run.id})
                raise

    def shortlist_for_month(self, month: str) -> List[ShortlistItem]:
        if not _is_valid_month(month):
            raise ValueError("invalid_month")

        with self._session_factory() as session:
            repo = Repository(session)
            projections = repo.shortlist_for_month(month)
            return [
                ShortlistItem(
                    drive_item_id=projection.photo.drive_item_id,
                    filename=projection.photo.filename,
                    captured_at=projection.photo.captured_at,
                    width=projection.photo.width,
                    height=projection.photo.height,
                    quality_score=projection.photo.quality_score,
                    download_url=projection.photo.download_url,
                    rank=projection.entry.rank,
                )
                for projection in projections
            ]

    # Internal helpers -----------------------------------------------------------

    def _process_items(
        self,
        *,
        session: Session,
        repo: Repository,
        items: Sequence[DriveItem],
        month_bucket: str,
        shortlist_limit: int,
    ) -> Tuple[RunTotals, List[Tuple[int, float]]]:
        total_items = 0
        eligible_items = 0
        shortlist_candidates: List[Tuple[int, float]] = []

        for item in items:
            total_items += 1

            captured_at = item.captured_at or item.last_modified
            item_month = _month_bucket(captured_at) if captured_at else None
            width = item.width or 0
            height = item.height or 0

            resolution_ok = _passes_resolution(width, height)
            matches_month = item_month == month_bucket
            eligible = resolution_ok and matches_month

            quality_score = float(width * height) if width and height else None

            photo = repo.upsert_photo(
                drive_item_id=item.id,
                drive_id=item.drive_id,
                filename=item.name,
                download_url=item.download_url,
                captured_at=captured_at,
                width=item.width,
                height=item.height,
                month=item_month,
                quality_score=quality_score,
                eligible=eligible,
            )

            if eligible and quality_score is not None:
                eligible_items += 1
                shortlist_candidates.append((photo.id, quality_score))

        shortlist_candidates.sort(key=lambda entry: entry[1], reverse=True)
        ranked = shortlist_candidates[:shortlist_limit]

        stats = RunTotals(
            total_items=total_items,
            eligible_items=eligible_items,
            shortlisted_items=len(ranked),
        )
        return stats, ranked


def _is_valid_month(value: str) -> bool:
    if len(value) != 7:
        return False
    try:
        datetime.strptime(value + "-01", "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _month_bucket(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m")


def _previous_month_string(today: Optional[date] = None) -> str:
    today = today or datetime.now(timezone.utc).date()
    first_of_month = today.replace(day=1)
    previous_month_last_day = first_of_month - timedelta(days=1)
    return previous_month_last_day.strftime("%Y-%m")


def _passes_resolution(width: int, height: int) -> bool:
    if width <= 0 or height <= 0:
        return False

    longest = max(width, height)
    shortest = min(width, height)
    return longest >= 1800 and shortest >= 1200
