"""Record repository skeleton."""
from __future__ import annotations
from typing import Iterable
from datetime import date
from ..models import Record, RecordType

class RecordRepository:
    """In a real app, implement via SQLAlchemy; here we keep a stub API."""
    def add(self, record: Record) -> Record:
        raise NotImplementedError

    def list_by_period(self, user_id: int, start: date, end: date) -> Iterable[Record]:
        raise NotImplementedError

    def search(self, user_id: int, keyword: str) -> Iterable[Record]:
        raise NotImplementedError
