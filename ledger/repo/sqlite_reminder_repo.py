from __future__ import annotations
from typing import Iterable
from sqlalchemy import select, insert
from sqlalchemy.orm import Session
from .sqlite_schema import reminders
from ..models import Reminder

class SqliteReminderRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, reminder: Reminder) -> Reminder:
        res = self._session.execute(insert(reminders).values(
            user_id=reminder.user_id,
            message=reminder.message,
            at=reminder.at,
            enabled=bool(reminder.enabled),
            frequency=reminder.frequency,
        ))
        pk = res.inserted_primary_key[0]
        self._session.commit()
        return Reminder(reminder_id=int(pk), user_id=reminder.user_id, message=reminder.message, at=reminder.at, enabled=bool(reminder.enabled), frequency=reminder.frequency)

    def list_enabled(self, user_id: int):
        rows = self._session.execute(select(
            reminders.c.reminder_id, reminders.c.user_id, reminders.c.message, reminders.c.at, reminders.c.enabled, reminders.c.frequency
        ).where((reminders.c.user_id == user_id) & (reminders.c.enabled == True)).order_by(reminders.c.at.asc())).all()
        return [Reminder(reminder_id=r.reminder_id, user_id=r.user_id, message=r.message, at=r.at, enabled=bool(r.enabled), frequency=r.frequency) for r in rows]
