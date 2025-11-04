from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..repo.sqlite_schema import metadata

_ENGINE = None
_SESSION_FACTORY = None


def get_engine(db_url: str = "sqlite:///./ledger.db"):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(db_url, echo=False, future=True)
    return _ENGINE


def get_session_factory(db_url: str = "sqlite:///./ledger.db"):
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        engine = get_engine(db_url)
        _SESSION_FACTORY = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, future=True
        )
    return _SESSION_FACTORY


def init_db(db_url: str = "sqlite:///./ledger.db") -> None:
    engine = get_engine(db_url)
    metadata.create_all(engine)
