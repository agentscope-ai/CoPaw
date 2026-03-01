# -*- coding: utf-8 -*-
"""Cron execution history — append-only JSONL storage."""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CronJobHistory(BaseModel):
    """A single execution record for a cron job."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    job_id: str
    started_at: float = Field(default_factory=time.time)
    finished_at: Optional[float] = None
    status: Literal["success", "error", "running"] = "running"
    error: Optional[str] = None
    attempt: int = 1


class HistoryRepo:
    """Append-only JSONL file for cron execution history.

    Each line is a JSON-serialized CronJobHistory record.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, record: CronJobHistory) -> None:
        """Append a history record to the JSONL file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

    def list_by_job(
        self,
        job_id: str,
        limit: int = 50,
    ) -> List[CronJobHistory]:
        """Return recent history for *job_id*, newest first."""
        if not self._path.exists():
            return []
        records: List[CronJobHistory] = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = CronJobHistory.model_validate(json.loads(line))
                        if rec.job_id == job_id:
                            records.append(rec)
                    except Exception:
                        continue
        except Exception:
            logger.exception("Failed to read cron history")
        # Newest first, limited
        records.reverse()
        return records[:limit]
