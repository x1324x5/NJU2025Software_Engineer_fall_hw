from __future__ import annotations
from typing import Iterable
from sqlalchemy import select, insert, update
from sqlalchemy.orm import Session
from .sqlite_schema import budgets
from ..models import Budget

class SqliteBudgetRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, budget: Budget) -> Budget:
        res = self._session.execute(insert(budgets).values(
            user_id=budget.user_id,
            category=budget.category,
            monthly_limit=float(budget.monthly_limit),
            period=budget.period,
        ))
        pk = res.inserted_primary_key[0]
        self._session.commit()
        return Budget(budget_id=int(pk), user_id=budget.user_id, category=budget.category, monthly_limit=float(budget.monthly_limit), period=budget.period)

    def list_by_user(self, user_id: int):
        rows = self._session.execute(select(
            budgets.c.budget_id, budgets.c.user_id, budgets.c.category, budgets.c.monthly_limit, budgets.c.period
        ).where(budgets.c.user_id == user_id).order_by(budgets.c.category.asc())).all()
        return [Budget(budget_id=r.budget_id, user_id=r.user_id, category=r.category, monthly_limit=float(r.monthly_limit), period=r.period) for r in rows]

    def get_by_category(self, user_id: int, category: str) -> Budget | None:
        row = self._session.execute(select(
            budgets.c.budget_id, budgets.c.user_id, budgets.c.category, budgets.c.monthly_limit, budgets.c.period
        ).where((budgets.c.user_id == user_id) & (budgets.c.category == category))).first()
        if not row:
            return None
        return Budget(budget_id=row.budget_id, user_id=row.user_id, category=row.category, monthly_limit=float(row.monthly_limit), period=row.period)

    def update_limit(self, budget_id: int, monthly_limit: float) -> None:
        self._session.execute(update(budgets).where(budgets.c.budget_id == budget_id).values(monthly_limit=float(monthly_limit)))
        self._session.commit()
