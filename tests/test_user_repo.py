import uuid
from ledger.utils.db import init_db, get_session_factory
from ledger.repo.sqlite_user_repo import SqliteUserRepository


def _make_session(db_url: str):
    init_db(db_url=db_url)
    SessionFactory = get_session_factory(db_url=db_url)
    return SessionFactory()


def test_user_register_and_get_by_name(tmp_path):
    db_url = f"sqlite:///{tmp_path}/user_{uuid.uuid4().hex}.db"
    session = _make_session(db_url)
    repo = SqliteUserRepository(session)

    uname = f"user_{uuid.uuid4().hex[:8]}"
    u = repo.register(uname, "123456", f"{uname}@example.com")
    assert u.user_id is not None

    got = repo.get_by_name(uname)
    assert got is not None
    assert got.name == uname
    assert got.email == f"{uname}@example.com"


def test_user_register_duplicate_raises(tmp_path):
    db_url = f"sqlite:///{tmp_path}/user_{uuid.uuid4().hex}.db"
    session = _make_session(db_url)
    repo = SqliteUserRepository(session)

    uname = f"user_{uuid.uuid4().hex[:8]}"
    repo.register(uname, "123456", f"{uname}@example.com")

    raised = False
    try:
        repo.register(uname, "abcdef", f"dup_{uname}@example.com")
    except ValueError:
        raised = True
    assert raised, "重复用户名应当抛 ValueError"
