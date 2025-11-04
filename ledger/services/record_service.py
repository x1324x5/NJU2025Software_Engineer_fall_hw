"""Record service: validation and orchestration."""
from __future__ import annotations
from dataclasses import asdict
from datetime import date
from typing import Iterable
from ..models import Record, RecordType
from ..repo.record_repo import RecordRepository

class RecordService:
    def __init__(self, repo: RecordRepository):
        self._repo = repo

    def create_record(self, rec: Record) -> Record:
        self._validate(rec)
        return self._repo.add(rec)

    def list_month(self, user_id: int, year: int, month: int) -> Iterable[Record]:
        start = date(year, month, 1)
        end = date(year + (month // 12), ((month % 12) + 1), 1)
        return self._repo.list_by_period(user_id, start, end)

    def _validate(self, rec: Record) -> None:
        if rec.amount <= 0:
            raise ValueError("amount must be positive")
        if not rec.category:
            raise ValueError("category required")
