# ledger/repo/sqlite_user_repo.py
from __future__ import annotations
from hashlib import sha256
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from .sqlite_schema import users
from ..models import User


def _hash_password(name: str, password: str) -> str:
    # 简单可复现的散列：以用户名作盐
    return sha256(f"{name}:{password}".encode("utf-8")).hexdigest()


class SqliteUserRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, user: User) -> User:
        # 兼容旧接口：add 不处理密码，只能插入一个占位 hash
        res = self._session.execute(
            insert(users).values(
                name=user.name,
                email=user.email,
                password_hash=_hash_password(user.name, ""),
            )
        )
        pk = res.inserted_primary_key[0]
        self._session.commit()
        return User(user_id=int(pk), name=user.name, email=user.email)

    def get_by_name(self, name: str) -> User | None:
        row = self._session.execute(
            select(users.c.user_id, users.c.name, users.c.email).where(
                users.c.name == name
            )
        ).first()
        if not row:
            return None
        return User(user_id=row.user_id, name=row.name, email=row.email)

    # 测试里会用到：第一次注册成功；同名则抛错
    def register(self, name: str, password: str, email: str | None = None) -> User:
        exists = self._session.execute(
            select(users.c.user_id).where(users.c.name == name)
        ).first()
        if exists:
            raise ValueError("username already exists")
        pwd_hash = _hash_password(name, password)
        res = self._session.execute(
            insert(users).values(name=name, email=email, password_hash=pwd_hash)
        )
        pk = res.inserted_primary_key[0]
        self._session.commit()
        return User(user_id=int(pk), name=name, email=email)

    # CLI 的 login 命令在用它
    def verify_login(self, name: str, password: str) -> User:
        row = self._session.execute(
            select(
                users.c.user_id, users.c.name, users.c.email, users.c.password_hash
            ).where(users.c.name == name)
        ).first()
        if not row:
            raise ValueError("user not found")
        if row.password_hash != _hash_password(name, password):
            raise ValueError("invalid credentials")
        return User(user_id=row.user_id, name=row.name, email=row.email)
