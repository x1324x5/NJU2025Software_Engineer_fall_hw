"""User repository skeleton."""
from __future__ import annotations
from ..models import User

class UserRepository:
    def add(self, user: User) -> User:
        raise NotImplementedError

    def get_by_name(self, name: str) -> User | None:
        raise NotImplementedError
