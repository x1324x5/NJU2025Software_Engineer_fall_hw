"""CSV I/O helpers for Record objects."""

from __future__ import annotations
import pandas as pd
from typing import Iterable
from pathlib import Path
from ..models import Record, RecordType


def load_records_from_csv(path: str) -> list[Record]:
    """
    Load records from a CSV file into a list of Record objects.
    Expected columns:
        record_id (optional), user_id, rtype, category, amount, occurred_on, note
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(p, dtype={"rtype": str, "category": str, "note": str})
    records: list[Record] = []

    for _, row in df.iterrows():
        try:
            rtype = (
                RecordType(row["rtype"])
                if not isinstance(row["rtype"], RecordType)
                else row["rtype"]
            )
        except Exception:
            raise ValueError(f"Invalid record type in row: {row.to_dict()}")

        record = Record(
            record_id=(
                int(row["record_id"])
                if "record_id" in row and not pd.isna(row["record_id"])
                else None
            ),
            user_id=int(row["user_id"]),
            rtype=rtype,
            category=str(row["category"]),
            amount=float(row["amount"]),
            occurred_on=pd.to_datetime(row["occurred_on"]).date(),
            note=str(row.get("note", "")) if "note" in row else "",
        )
        records.append(record)

    return records


def save_records_to_csv(path: str, records: Iterable[Record]) -> None:
    """
    Save records to a CSV file.
    Converts Enum and date fields to string for readability.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for r in records:
        rows.append(
            {
                "record_id": r.record_id if r.record_id is not None else "",
                "user_id": r.user_id,
                "rtype": r.rtype.value if hasattr(r.rtype, "value") else str(r.rtype),
                "category": r.category,
                "amount": float(r.amount),
                "occurred_on": r.occurred_on.isoformat(),
                "note": r.note or "",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding="utf-8")
