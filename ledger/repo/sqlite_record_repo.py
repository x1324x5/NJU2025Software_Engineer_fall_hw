"""SQLite-backed RecordRepository implementation using SQLAlchemy Core."""
from __future__ import annotations
from typing import Iterable
from datetime import date
from sqlalchemy import select, insert, and_, or_
from sqlalchemy.orm import Session
from .record_repo import RecordRepository
from .sqlite_schema import records
from ..models import Record, RecordType

class SqliteRecordRepository(RecordRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, record: Record) -> Record:
        stmt = insert(records).values(
            user_id=record.user_id,
            rtype=record.rtype.value,
            category=record.category,
            amount=float(record.amount),
            occurred_on=record.occurred_on,
            note=record.note or "",
        )
        result = self._session.execute(stmt)
        pk = result.inserted_primary_key[0]
        self._session.commit()
        return Record(
            record_id=int(pk),
            user_id=record.user_id,
            rtype=record.rtype,
            category=record.category,
            amount=float(record.amount),
            occurred_on=record.occurred_on,
            note=record.note or "",
        )

    def list_by_period(self, user_id: int, start: date, end: date) -> Iterable[Record]:
        q = (
            select(
                records.c.record_id,
                records.c.user_id,
                records.c.rtype,
                records.c.category,
                records.c.amount,
                records.c.occurred_on,
                records.c.note,
            )
            .where(
                and_(
                    records.c.user_id == user_id,
                    records.c.occurred_on >= start,
                    records.c.occurred_on < end,
                )
            )
            .order_by(records.c.occurred_on.asc(), records.c.record_id.asc())
        )
        rows = self._session.execute(q).all()
        return [
            Record(
                record_id=row.record_id,
                user_id=row.user_id,
                rtype=RecordType(row.rtype),
                category=row.category,
                amount=float(row.amount),
                occurred_on=row.occurred_on,
                note=row.note or "",
            )
            for row in rows
        ]

    def search(self, user_id: int, keyword: str) -> Iterable[Record]:
        like = f"%{keyword}%"
        q = (
            select(
                records.c.record_id,
                records.c.user_id,
                records.c.rtype,
                records.c.category,
                records.c.amount,
                records.c.occurred_on,
                records.c.note,
            )
            .where(
                and_(
                    records.c.user_id == user_id,
                    or_(
                        records.c.category.like(like),
                        records.c.note.like(like),
                    ),
                )
            )
            .order_by(records.c.occurred_on.desc(), records.c.record_id.desc())
        )
        rows = self._session.execute(q).all()
        return [
            Record(
                record_id=row.record_id,
                user_id=row.user_id,
                rtype=RecordType(row.rtype),
                category=row.category,
                amount=float(row.amount),
                occurred_on=row.occurred_on,
                note=row.note or "",
            )
            for row in rows
        ]
