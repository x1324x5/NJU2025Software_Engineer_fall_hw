from __future__ import annotations
from typing import Iterable, Dict
from ..models import Budget, Record, RecordType


class BudgetService:
    def progress(
        self, budgets: Iterable[Budget], records: Iterable[Record]
    ) -> Dict[str, float]:
        spent = {b.category: 0.0 for b in budgets}
        for r in records:
            if r.rtype == RecordType.EXPENSE and r.category in spent:
                spent[r.category] += float(r.amount)
        return {
            b.category: (
                0.0
                if b.monthly_limit <= 0
                else round(spent[b.category] / float(b.monthly_limit), 4)
            )
            for b in budgets
        }

    def alert_flags(
        self,
        budgets: Iterable[Budget],
        records: Iterable[Record],
        warn_ratio: float = 0.8,
    ) -> Dict[str, bool]:
        prog = self.progress(budgets, records)
        return {cat: (ratio >= warn_ratio) for cat, ratio in prog.items()}
