"""Budget repository skeleton."""
from __future__ import annotations
from typing import Iterable
from ..models import Budget

class BudgetRepository:
    def add(self, budget: Budget) -> Budget:
        raise NotImplementedError

    def list_by_user(self, user_id: int) -> Iterable[Budget]:
        raise NotImplementedError
