from datetime import date
from sqlalchemy.orm import Session
from ledger.utils.db import get_session_factory, init_db
from ledger.repo.sqlite_user_repo import SqliteUserRepository
from ledger.repo.sqlite_record_repo import SqliteRecordRepository
from ledger.models import User, Record, RecordType


def make_session(db_url: str) -> Session:
    init_db(db_url=db_url)
    SessionFactory = get_session_factory(db_url=db_url)
    return SessionFactory()


def test_add_and_query_records(tmp_path):
    db_url = f"sqlite:///{tmp_path}/m1_test.db"
    session = make_session(db_url)
    # user
    urepo = SqliteUserRepository(session)
    user = urepo.add(User(None, "alice", "a@example.com"))

    rrepo = SqliteRecordRepository(session)
    # add
    r1 = rrepo.add(
        Record(
            None,
            user.user_id,
            RecordType.EXPENSE,
            "food",
            25.5,
            date(2025, 1, 2),
            "lunch",
        )
    )
    r2 = rrepo.add(
        Record(
            None,
            user.user_id,
            RecordType.EXPENSE,
            "transport",
            10.0,
            date(2025, 1, 3),
            "bus",
        )
    )
    r3 = rrepo.add(
        Record(
            None,
            user.user_id,
            RecordType.INCOME,
            "salary",
            1000.0,
            date(2025, 1, 1),
            "Jan",
        )
    )

    # list by period (Jan 2025)
    recs = list(rrepo.list_by_period(user.user_id, date(2025, 1, 1), date(2025, 2, 1)))
    assert len(recs) == 3
    # search
    found = list(rrepo.search(user.user_id, "foo"))
    assert len(found) == 1
    assert found[0].category == "food"
