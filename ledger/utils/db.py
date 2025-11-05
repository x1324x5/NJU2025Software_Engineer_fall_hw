# ledger/utils/db.py
"""Engine / SessionFactory per-URL cache + init helpers."""
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..repo.sqlite_schema import (
    metadata,
)  # 如果你用 ORM，请改成 from ..utils.schema import Base

# 关键：按 db_url 维度缓存，而不是单例
_ENGINE_CACHE: dict[str, object] = {}
_SESSION_FACTORY_CACHE: dict[str, object] = {}


def get_engine(db_url: str = "sqlite:///./ledger.db"):
    engine = _ENGINE_CACHE.get(db_url)
    if engine is None:
        engine = create_engine(db_url, echo=False, future=True)
        _ENGINE_CACHE[db_url] = engine
    return engine


def get_session_factory(db_url: str = "sqlite:///./ledger.db"):
    fac = _SESSION_FACTORY_CACHE.get(db_url)
    if fac is None:
        engine = get_engine(db_url)
        fac = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        _SESSION_FACTORY_CACHE[db_url] = fac
    return fac


def init_db(db_url: str = "sqlite:///./ledger.db") -> None:
    engine = get_engine(db_url)
    metadata.create_all(engine)  # ORM 版用：Base.metadata.create_all(engine)


# 可选：测试时重置缓存
def reset_db_cache() -> None:
    _ENGINE_CACHE.clear()
    _SESSION_FACTORY_CACHE.clear()
