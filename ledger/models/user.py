"""User entity."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class User:
    """Represents an application user."""
    user_id: int | None
    name: str
    email: str | None = None
