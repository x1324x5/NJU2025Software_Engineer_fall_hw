"""Budget service: progress and alerts."""
from __future__ import annotations
from typing import Iterable, Dict
from ..models import Budget, Record, RecordType

class BudgetService:
    def progress(self, budgets: Iterable[Budget], records: Iterable[Record]) -> Dict[str, float]:
        """Return category->(spent/limit) ratio in [0, +inf)."""
        spent = {b.category: 0.0 for b in budgets}
        for r in records:
            if r.rtype == RecordType.EXPENSE and r.category in spent:
                spent[r.category] += r.amount
        return {b.category: (0.0 if b.monthly_limit <= 0 else round(spent[b.category] / b.monthly_limit, 4)) for b in budgets}
