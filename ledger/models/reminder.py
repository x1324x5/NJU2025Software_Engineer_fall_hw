"""Reminder entity."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import time

@dataclass(slots=True)
class Reminder:
    reminder_id: int | None
    user_id: int
    message: str
    at: time
    enabled: bool = True
