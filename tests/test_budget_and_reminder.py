from datetime import date, time
from sqlalchemy.orm import Session
from ledger.utils.db import init_db, get_session_factory
from ledger.repo.sqlite_user_repo import SqliteUserRepository
from ledger.repo.sqlite_budget_repo import SqliteBudgetRepository
from ledger.repo.sqlite_reminder_repo import SqliteReminderRepository
from ledger.models import User, Record, RecordType, Budget, Reminder
from ledger.services.budget_service import BudgetService
from ledger.services.reminder_service import ReminderService

def make_session(db_url: str) -> Session:
    init_db(db_url=db_url)
    SessionFactory = get_session_factory(db_url=db_url)
    return SessionFactory()

def test_budget_progress_and_alerts(tmp_path):
    db_url = f"sqlite:///{tmp_path}/br_test.db"
    session = make_session(db_url)
    u = SqliteUserRepository(session).add(User(None, "bob", "b@example.com"))

    b_repo = SqliteBudgetRepository(session)
    food = b_repo.add(Budget(None, u.user_id, "food", 300.0, "MONTHLY"))
    rent = b_repo.add(Budget(None, u.user_id, "rent", 1500.0, "MONTHLY"))

    recs = [
        Record(None, u.user_id, RecordType.EXPENSE, "food", 120.0, date(2025,1,2), ""),
        Record(None, u.user_id, RecordType.EXPENSE, "food", 80.0, date(2025,1,3), ""),
        Record(None, u.user_id, RecordType.EXPENSE, "rent", 1200.0, date(2025,1,1), ""),
        Record(None, u.user_id, RecordType.INCOME, "salary", 5000.0, date(2025,1,1), ""),
    ]
    svc = BudgetService()
    prog = svc.progress([food, rent], recs)
    assert 0.65 <= prog["food"] <= 0.67
    alerts = svc.alert_flags([food, rent], recs, warn_ratio=0.8)
    assert alerts["food"] is False and alerts["rent"] is False

    b_repo.update_limit(food.budget_id, 200.0)
    food2 = b_repo.get_by_category(u.user_id, "food")
    prog2 = svc.progress([food2, rent], recs)
    assert 0.99 <= prog2["food"] <= 1.01
    alerts2 = svc.alert_flags([food2, rent], recs, warn_ratio=0.8)
    assert alerts2["food"] is True

def test_reminder_add_and_list(tmp_path, capsys):
    db_url = f"sqlite:///{tmp_path}/br_test2.db"
    session = make_session(db_url)
    u = SqliteUserRepository(session).add(User(None, "carol", "c@example.com"))

    r_repo = SqliteReminderRepository(session)
    r_repo.add(Reminder(None, u.user_id, "Log expenses", time(hour=21, minute=0), True, "DAILY"))
    r_repo.add(Reminder(None, u.user_id, "Weekly summary", time(hour=9, minute=0), True, "WEEKLY"))

    svc = ReminderService()
    svc.emit(r_repo.list_enabled(u.user_id))
    out = capsys.readouterr().out
    assert "Log expenses" in out and "Weekly summary" in out
