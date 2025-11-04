"""Budget entity."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class Budget:
    budget_id: int | None
    user_id: int
    category: str
    monthly_limit: float
