from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from typing import Optional
from uuid import UUID, uuid4

from app.models import PhotoResult, ScanOutcome, ScanRequest, ScanState, ScanStatus
from app.services.scanner import run_scan
from app.services.thumbnails import ensure_thumbnails_for_results, remove_thumbnails_for_scan

logger = logging.getLogger(__name__)


class ScanManager:
    """Manage scan job lifecycle and background execution."""

    def __init__(self, max_workers: int = 4, history_limit: int = 5) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="photo-archivist")
        self._lock = Lock()
        self._statuses: dict[UUID, ScanStatus] = {}
        self._outcomes: dict[UUID, ScanOutcome] = {}
        self._history_limit = max(0, history_limit)
        self._shutdown = False

    def enqueue(self, request: ScanRequest) -> UUID:
        scan_id = uuid4()
        status = ScanStatus(id=scan_id, state=ScanState.QUEUED)
        with self._lock:
            self._statuses[scan_id] = status
        self._executor.submit(self._execute_scan, scan_id, request)
        return scan_id

    def get_status(self, scan_id: UUID) -> Optional[ScanStatus]:
        with self._lock:
            status = self._statuses.get(scan_id)
        if status is None:
            return None
        return replace(status)

    def get_outcome(self, scan_id: UUID) -> Optional[ScanOutcome]:
        with self._lock:
            outcome = self._outcomes.get(scan_id)
        if outcome is None:
            return None
        return ScanOutcome(
            results=list(outcome.results),
            total_files=outcome.total_files,
            matched_files=outcome.matched_files,
            discarded_files=outcome.discarded_files,
        )

    def get_selected_results(self, scan_id: UUID) -> list[PhotoResult]:
        with self._lock:
            outcome = self._outcomes.get(scan_id)
            if outcome is None:
                return []
            return [photo for photo in outcome.results if photo.selected]

    def snapshot(self, scan_id: UUID) -> tuple[Optional[ScanStatus], Optional[ScanOutcome]]:
        with self._lock:
            status = self._statuses.get(scan_id)
            outcome = self._outcomes.get(scan_id)
        status_copy = replace(status) if status is not None else None
        outcome_copy = (
            ScanOutcome(
                results=list(outcome.results),
                total_files=outcome.total_files,
                matched_files=outcome.matched_files,
                discarded_files=outcome.discarded_files,
            )
            if outcome is not None
            else None
        )
        return status_copy, outcome_copy

    def _execute_scan(self, scan_id: UUID, request: ScanRequest) -> None:
        self._update_status(scan_id, state=ScanState.RUNNING)

        def handle_progress(processed: int, total: int, matched: int) -> None:
            self._update_status(scan_id, processed=processed, total=total, matched=matched)

        try:
            outcome = run_scan(request, progress_callback=handle_progress)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Scan %s failed: %s", scan_id, exc)
            self._update_status(scan_id, state=ScanState.ERROR, message=str(exc))
            return

        try:
            ensure_thumbnails_for_results(scan_id, outcome.results)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Thumbnail generation failed for scan %s: %s", scan_id, exc)
            self._update_status(scan_id, message="Some thumbnails could not be generated.")

        with self._lock:
            self._outcomes[scan_id] = outcome

        self._update_status(
            scan_id,
            state=ScanState.COMPLETE,
            processed=outcome.total_files,
            total=outcome.total_files,
            matched=outcome.matched_files,
        )
        self._prune_completed_history()

    def _update_status(self, scan_id: UUID, **updates) -> None:
        with self._lock:
            status = self._statuses.get(scan_id)
            if status is None:
                return
            for field_name, value in updates.items():
                setattr(status, field_name, value)
            status.updated_at = datetime.now(timezone.utc)

    def set_selection(
        self, scan_id: UUID, photo_id: UUID, selected: bool
    ) -> tuple[Optional[ScanStatus], Optional[ScanOutcome], bool]:
        with self._lock:
            status = self._statuses.get(scan_id)
            outcome = self._outcomes.get(scan_id)
            if status is None or outcome is None:
                return None, None, False

            target = next((item for item in outcome.results if item.id == photo_id), None)
            if target is None:
                return replace(status), ScanOutcome(
                    results=list(outcome.results),
                    total_files=outcome.total_files,
                    matched_files=outcome.matched_files,
                    discarded_files=outcome.discarded_files,
                ), False

            target.selected = selected
            return (
                replace(status),
                ScanOutcome(
                    results=list(outcome.results),
                    total_files=outcome.total_files,
                    matched_files=outcome.matched_files,
                    discarded_files=outcome.discarded_files,
                ),
                True,
            )

    def shutdown(self) -> None:
        """Stop background workers and release cached scan data."""
        if not self._shutdown:
            self._executor.shutdown(wait=True, cancel_futures=False)
            self._shutdown = True
        removed_ids = self._drain_all_scans()
        for scan_id in removed_ids:
            remove_thumbnails_for_scan(scan_id)

    def _prune_completed_history(self) -> None:
        if self._history_limit <= 0:
            return

        with self._lock:
            completed_items = [
                (scan_id, status)
                for scan_id, status in self._statuses.items()
                if status.state in (ScanState.COMPLETE, ScanState.ERROR)
            ]
            if len(completed_items) <= self._history_limit:
                return

            completed_items.sort(key=lambda item: item[1].updated_at, reverse=True)
            to_remove = [scan_id for scan_id, _ in completed_items[self._history_limit :]]

            for scan_id in to_remove:
                self._statuses.pop(scan_id, None)
                self._outcomes.pop(scan_id, None)

        for scan_id in to_remove:
            remove_thumbnails_for_scan(scan_id)

    def _drain_all_scans(self) -> list[UUID]:
        with self._lock:
            outcome_ids = list(self._outcomes.keys())
            self._statuses.clear()
            self._outcomes.clear()
        return outcome_ids
