from __future__ import annotations
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from .sqlite_schema import users
from ..models import User

class SqliteUserRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, user: User) -> User:
        res = self._session.execute(insert(users).values(name=user.name, email=user.email))
        pk = res.inserted_primary_key[0]
        self._session.commit()
        return User(user_id=int(pk), name=user.name, email=user.email)

    def get_by_name(self, name: str) -> User | None:
        row = self._session.execute(select(users.c.user_id, users.c.name, users.c.email).where(users.c.name == name)).first()
        if not row:
            return None
        return User(user_id=row.user_id, name=row.name, email=row.email)
