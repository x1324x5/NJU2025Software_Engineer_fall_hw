from __future__ import annotations
from typing import Iterable
from ..models import Reminder


class ReminderRepository:
    def add(self, reminder: Reminder) -> Reminder: ...
    def list_enabled(self, user_id: int) -> Iterable[Reminder]: ...
