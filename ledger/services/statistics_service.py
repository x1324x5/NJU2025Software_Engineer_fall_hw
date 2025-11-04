"""Statistics service: aggregations for dashboard and charts."""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable, Dict
from ..models import Record, RecordType

class StatisticsService:
    def monthly_summary(self, records: Iterable[Record]) -> Dict[str, float]:
        """Return {'income': x, 'expense': y, 'balance': x-y}."""
        income = 0.0
        expense = 0.0
        for r in records:
            if r.rtype == RecordType.INCOME:
                income += r.amount
            else:
                expense += r.amount
        return {"income": round(income, 2), "expense": round(expense, 2), "balance": round(income - expense, 2)}

    def by_category(self, records: Iterable[Record]) -> Dict[str, float]:
        buckets: Dict[str, float] = defaultdict(float)
        for r in records:
            if r.rtype == RecordType.EXPENSE:
                buckets[r.category] += r.amount
        return {k: round(v, 2) for k, v in buckets.items()}
