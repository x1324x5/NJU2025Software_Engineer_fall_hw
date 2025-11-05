"""
Auth helpers: password hashing/verification + local session storage.

- Password hash format: "salt$sha256(salt+password)"
- Session file: ~/.ledger_session.json  -> {"db": "...", "user": "alice"}
"""

from __future__ import annotations

import json
import os
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SESSION_PATH = Path.home() / ".ledger_session.json"


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_password(password: str, *, salt: Optional[str] = None) -> str:
    """
    Return "salt$hash" string. Use os.urandom(16) for salt when not provided.
    """
    if salt is None:
        salt = os.urandom(16).hex()
    digest = _sha256_hex((salt + password).encode("utf-8"))
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify the "salt$hash" format.
    """
    try:
        salt, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    return _sha256_hex((salt + password).encode("utf-8")) == digest


# -------- session (simple local login) --------
@dataclass
class SessionData:
    db: str
    user: str


def save_session(db_url: str, username: str) -> None:
    SESSION_PATH.write_text(
        json.dumps({"db": db_url, "user": username}, ensure_ascii=False),
        encoding="utf-8",
    )


def load_session() -> Optional[SessionData]:
    if not SESSION_PATH.exists():
        return None
    try:
        obj = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        return SessionData(db=obj["db"], user=obj["user"])
    except Exception:
        return None


def clear_session() -> None:
    try:
        SESSION_PATH.unlink()
    except FileNotFoundError:
        pass
