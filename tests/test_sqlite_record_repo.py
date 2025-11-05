import uuid
from datetime import date
from ledger.utils.db import init_db, get_session_factory
from ledger.repo.sqlite_user_repo import SqliteUserRepository
from ledger.repo.sqlite_record_repo import SqliteRecordRepository
from ledger.models import Record, RecordType


def make_session(db_url: str):
    init_db(db_url=db_url)
    SessionFactory = get_session_factory(db_url=db_url)
    return SessionFactory()


def test_add_and_query_records(tmp_path):
    db_url = f"sqlite:///{tmp_path}/m1_{uuid.uuid4().hex}.db"
    session = make_session(db_url)

    # 用 register，且使用随机用户名，避免与预置数据冲突
    urepo = SqliteUserRepository(session)
    uname = f"user_{uuid.uuid4().hex[:6]}"
    user = urepo.register(uname, "123456", f"{uname}@example.com")

    rrepo = SqliteRecordRepository(session)

    r1 = Record(
        None,
        user.user_id,
        RecordType.INCOME,
        "salary",
        1000.0,
        date(2025, 1, 1),
        "monthly",
    )
    r2 = Record(
        None, user.user_id, RecordType.EXPENSE, "food", 50.5, date(2025, 1, 2), "lunch"
    )

    r1 = rrepo.add(r1)
    r2 = rrepo.add(r2)

    assert r1.record_id is not None and r2.record_id is not None

    recs = list(rrepo.list_month(user.user_id, 2025, 1))
    cats = {(r.category, r.rtype.name) for r in recs}
    assert ("salary", "INCOME") in cats
    assert ("food", "EXPENSE") in cats
