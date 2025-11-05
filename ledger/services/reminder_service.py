# ledger/services/reminder_service.py
from __future__ import annotations
from typing import Iterable
from ..models import Reminder


class ReminderService:
    def emit(self, reminders: Iterable[Reminder]) -> None:
        for r in reminders:
            if r.enabled:
                # 仅输出时间与消息（不再访问 r.frequency）
                print(f"[reminder] {r.at.isoformat()} - {r.message}")
