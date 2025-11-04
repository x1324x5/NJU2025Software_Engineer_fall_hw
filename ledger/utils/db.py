"""Database utilities: create engine and session factory."""

from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..repo.sqlite_schema import metadata

_ENGINE = None
_SESSION_FACTORY = None


def get_engine(db_url: str = "sqlite:///./ledger.db"):
    """Return a cached SQLAlchemy engine."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(db_url, echo=False, future=True)
    return _ENGINE


def get_session_factory(db_url: str = "sqlite:///./ledger.db"):
    """Return a cached session factory bound to the engine."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        engine = get_engine(db_url)
        _SESSION_FACTORY = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, future=True
        )
    return _SESSION_FACTORY


def init_db(db_url: str = "sqlite:///./ledger.db") -> None:
    """Create all tables if they do not exist."""

    engine = get_engine(db_url)
    metadata.create_all(engine)
