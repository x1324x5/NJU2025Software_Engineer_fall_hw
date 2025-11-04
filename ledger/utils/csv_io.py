"""CSV I/O helper stubs for records and budgets."""
from __future__ import annotations
from typing import Iterable
from ..models import Record, Budget

def load_records_from_csv(path: str) -> list[Record]:
    """TODO: parse CSV and construct Record objects."""
    raise NotImplementedError

def save_records_to_csv(path: str, records: Iterable[Record]) -> None:
    """TODO: write records to CSV."""
    raise NotImplementedError
