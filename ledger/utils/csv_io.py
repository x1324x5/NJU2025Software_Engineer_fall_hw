"""CSV I/O helper stubs for records and budgets."""

from __future__ import annotations
from typing import Iterable
from ..models import Record, Budget
import pandas as pd


def load_records_from_csv(path: str) -> list[Record]:
    """TODO: parse CSV and construct Record objects."""
    data = pd.read_csv(path)
    records = []
    for _, row in data.iterrows():
        record = Record(
            record_id=row.get("record_id", None),
            user_id=row["user_id"],
            rtype=row["rtype"],
            category=row["category"],
            amount=row["amount"],
            occurred_on=pd.to_datetime(row["occurred_on"]).date(),
            note=row.get("note", ""),
        )
        records.append(record)
    return records


def save_records_to_csv(path: str, records: Iterable[Record]) -> None:
    """TODO: write records to CSV."""
    data = pd.DataFrame([r.__dict__ for r in records])
    data.to_csv(path, index=False)
