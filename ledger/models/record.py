"""Record entity for incomes/expenses."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import date

class RecordType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

@dataclass(slots=True)
class Record:
    record_id: int | None
    user_id: int
    rtype: RecordType
    category: str
    amount: float
    occurred_on: date
    note: str = ""
