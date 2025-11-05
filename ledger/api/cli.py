"""
Ledger CLI with authentication.
- 支持：register/login/logout/whoami/change-password
- 记录：add/list/stats/import-csv/export-csv（需已登录）
- 预算：budget set/list/progress（需已登录）
- 提醒：reminder set/list/emit（需已登录）
"""

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import date, datetime, time
from typing import Iterable, Tuple

try:
    import matplotlib.pyplot as plt  # 仅在 --plot 时使用
except Exception:  # pragma: no cover
    plt = None

from ..utils.db import init_db, get_session_factory
from ..repo.sqlite_user_repo import SqliteUserRepository
from ..repo.sqlite_record_repo import SqliteRecordRepository
from ..repo.sqlite_schema import budgets, reminders
from ..models import Record, RecordType, User, Budget, Reminder
from ..services.statistics_service import StatisticsService
from ..services.record_service import RecordService
from ..services.budget_service import BudgetService
from ..services.reminder_service import ReminderService
from ..utils.auth import save_session, load_session, clear_session, SessionData

# csv io
try:
    from ..utils.csv_io import load_records_from_csv, save_records_to_csv
except Exception:  # pragma: no cover
    load_records_from_csv = None
    save_records_to_csv = None


# ---------- helpers ----------
def _parse_month(s: str) -> Tuple[int, int]:
    try:
        dt = datetime.strptime(s, "%Y-%m")
        return dt.year, dt.month
    except ValueError as exc:
        raise argparse.ArgumentTypeError("month must be YYYY-MM") from exc


def _ensure_reports_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _get_session(db_url: str):
    init_db(db_url=db_url)
    SessionFactory = get_session_factory(db_url=db_url)
    return SessionFactory()


def _require_login(db_url: str) -> SessionData:
    sess = load_session()
    if not sess:
        raise SystemExit(
            "not logged in. run: python -m ledger.api.cli login --db <url> --username <name> --password <pw>"
        )
    if sess.db != db_url:
        raise SystemExit(
            f"logged in for a different DB: {sess.db}. please login again with --db {db_url}."
        )
    return sess


def _get_current_user(session, username: str) -> User:
    urepo = SqliteUserRepository(session)
    user = urepo.get_by_name(username)
    if not user:
        raise SystemExit("current user not found. please register/login again.")
    return user


# ---------- auth commands ----------
def cmd_register(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    urepo = SqliteUserRepository(session)
    try:
        u = urepo.register(args.username, args.password, args.email)
    except ValueError as e:
        raise SystemExit(str(e))
    print(f"registered user: {u.name} (id={u.user_id})")


def cmd_login(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    urepo = SqliteUserRepository(session)
    user = urepo.verify_login(args.username, args.password)
    if not user:
        raise SystemExit("invalid username or password")
    save_session(args.db, args.username)
    print(f"login ok: {args.username}")


def cmd_logout(args: argparse.Namespace) -> None:
    clear_session()
    print("logged out.")


def cmd_whoami(args: argparse.Namespace) -> None:
    sess = load_session()
    if not sess:
        print("not logged in")
    else:
        print(f"user={sess.user} db={sess.db}")


def cmd_change_password(args: argparse.Namespace) -> None:
    sess = _require_login(args.db)
    session = _get_session(args.db)
    urepo = SqliteUserRepository(session)
    ok = urepo.change_password(sess.user, args.old, args.new)
    if not ok:
        raise SystemExit("old password incorrect or user missing")
    print("password changed.")


# ---------- record commands (login required) ----------
def cmd_add(args: argparse.Namespace) -> None:
    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    r = Record(
        record_id=None,
        user_id=user.user_id,
        rtype=RecordType(args.type),
        category=args.category,
        amount=float(args.amount),
        occurred_on=date.fromisoformat(args.date),
        note=args.note or "",
    )
    created = svc.create_record(r)
    print(
        f"added record #{created.record_id}: {created.rtype} {created.category} "
        f"{created.amount} on {created.occurred_on.isoformat()}"
    )


def _iter_month_records(session, user: User, year: int, month: int) -> Iterable[Record]:
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    return svc.list_month(user.user_id, year, month)


def cmd_list(args: argparse.Namespace) -> None:
    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    year, month = _parse_month(args.month)
    recs = list(_iter_month_records(session, user, year, month))
    if not recs:
        print("no records")
        return
    for r in recs:
        print(
            f"#{r.record_id}\t{r.occurred_on.isoformat()}\t{r.rtype}\t"
            f"{r.category}\t{r.amount:.2f}\t{r.note}"
        )


def cmd_stats(args: argparse.Namespace) -> None:
    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    year, month = _parse_month(args.month)
    recs = list(_iter_month_records(session, user, year, month))
    svc = StatisticsService()
    summary = svc.monthly_summary(recs)
    by_cat = svc.by_category(recs)

    print(f"Summary for {user.name} {year}-{month:02d}")
    print(f"  income : {summary['income']:.2f}")
    print(f"  expense: {summary['expense']:.2f}")
    print(f"  balance: {summary['balance']:.2f}")
    if by_cat:
        print("  expense by category:")
        for k, v in by_cat.items():
            print(f"    {k}: {v:.2f}")

    if args.plot:
        reports_dir = Path(args.reports_dir or "reports")
        _ensure_reports_dir(reports_dir)
        labels = list(by_cat.keys())
        values = list(by_cat.values())
        if values:
            import matplotlib.pyplot as plt  # ensure available in function scope

            plt.figure()
            plt.pie(values, labels=labels, autopct="%1.1f%%")  # 不显式设置颜色
            out = reports_dir / f"expenses_by_category_{year}-{month:02d}.png"
            plt.title(f"Expenses by Category {year}-{month:02d}")
            plt.savefig(out, bbox_inches="tight")
            plt.close()
            print(f"saved plot: {out}")


# ---------- budgets (login required) ----------
def cmd_budget_set(args: argparse.Namespace) -> None:
    from sqlalchemy import insert

    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    session.execute(
        budgets.delete().where(
            budgets.c.user_id == user.user_id, budgets.c.category == args.category
        )
    )
    session.execute(
        insert(budgets).values(
            user_id=user.user_id,
            category=args.category,
            monthly_limit=float(args.limit),
        )
    )
    session.commit()
    print(f"budget set: category={args.category} limit={float(args.limit):.2f}")


def cmd_budget_list(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    rows = session.execute(
        select(budgets.c.category, budgets.c.monthly_limit).where(
            budgets.c.user_id == user.user_id
        )
    ).all()
    if not rows:
        print("no budgets")
        return
    for row in rows:
        print(f"{row.category}\t{row.monthly_limit:.2f}")


def cmd_budget_progress(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    year, month = _parse_month(args.month)

    b_rows = session.execute(
        select(budgets.c.category, budgets.c.monthly_limit).where(
            budgets.c.user_id == user.user_id
        )
    ).all()
    if not b_rows:
        print("no budgets")
        return

    recs = list(_iter_month_records(session, user, year, month))
    b_objs = [
        Budget(None, user.user_id, row.category, float(row.monthly_limit))
        for row in b_rows
    ]
    svc = BudgetService()
    prog = svc.progress(b_objs, recs)
    print(f"Budget progress for {user.name} {year}-{month:02d}")
    for cat in sorted(prog.keys()):
        ratio = prog[cat]
        pct = ratio * 100.0
        flag = " !!" if ratio >= 0.8 else ""  # 80% 预警
        print(f"  {cat}: {pct:.1f}%{flag}")


# ---------- reminders (login required) ----------
def cmd_reminder_set(args: argparse.Namespace) -> None:
    from sqlalchemy import insert

    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    at = time.fromisoformat(args.time)
    msg = args.message or "记账提醒"
    enabled = True if args.enabled else False if args.disable else True
    session.execute(
        insert(reminders).values(
            user_id=user.user_id, message=msg, at=at, enabled=enabled
        )
    )
    session.commit()
    print(f"reminder added: {at.isoformat()} - {msg} (enabled={enabled})")


def cmd_reminder_list(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    rows = session.execute(
        select(
            reminders.c.reminder_id,
            reminders.c.message,
            reminders.c.at,
            reminders.c.enabled,
        )
        .where(reminders.c.user_id == user.user_id)
        .order_by(reminders.c.at.asc())
    ).all()
    if not rows:
        print("no reminders")
        return
    for r in rows:
        status = "ON" if r.enabled else "OFF"
        print(f"#{r.reminder_id}\t{r.at}\t{status}\t{r.message}")


def cmd_reminder_emit(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    rows = session.execute(
        select(reminders.c.message, reminders.c.at, reminders.c.enabled).where(
            reminders.c.user_id == user.user_id
        )
    ).all()
    enabled_rows = [r for r in rows if r.enabled]
    svc = ReminderService()
    r_objs = [Reminder(None, user.user_id, r.message, r.at, True) for r in enabled_rows]
    svc.emit(r_objs)


# ---------- CSV (login required) ----------
def cmd_import_csv(args: argparse.Namespace) -> None:
    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    records = load_records_from_csv(args.path)
    count = 0
    for r in records:
        r = Record(
            None,
            user.user_id,
            r.rtype,
            r.category,
            float(r.amount),
            r.occurred_on,
            r.note or "",
        )
        svc.create_record(r)
        count += 1
    print(f"imported {count} records for user {user.name}")


def cmd_export_csv(args: argparse.Namespace) -> None:
    sess = _require_login(args.db)
    session = _get_session(args.db)
    user = _get_current_user(session, sess.user)
    year, month = _parse_month(args.month) if args.month else (None, None)
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    if year and month:
        recs = list(svc.list_month(user.user_id, year, month))
    else:
        recs = list(
            repo.list_by_period(user.user_id, date(1900, 1, 1), date(3000, 1, 1))
        )
    Path(args.path).parent.mkdir(parents=True, exist_ok=True)
    save_records_to_csv(args.path, recs)
    print(f"exported {len(recs)} records to {args.path}")


def cmd_init_db(args: argparse.Namespace) -> None:
    init_db(db_url=args.db)
    print(f"Initialized database at {args.db}")


# ---------- main ----------
def main() -> None:
    # 公共父解析器：让 --db 对所有子命令可见（写在子命令前后都行）
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--db",
        default="sqlite:///./ledger.db",
        help="SQLAlchemy DB URL (e.g. sqlite:///./ledger.db)",
    )

    parser = argparse.ArgumentParser(description="Ledger CLI (with login)")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser(
        "init-db", help="Create tables if not exist", parents=[common]
    )
    p_init.set_defaults(func=cmd_init_db)

    # auth
    p_reg = sub.add_parser("register", help="Register a new user", parents=[common])
    p_reg.add_argument("--username", required=True)
    p_reg.add_argument("--password", required=True)
    p_reg.add_argument("--email", required=False, default=None)
    p_reg.set_defaults(func=cmd_register)

    p_login = sub.add_parser("login", help="Login and store session", parents=[common])
    p_login.add_argument("--username", required=True)
    p_login.add_argument("--password", required=True)
    p_login.set_defaults(func=cmd_login)

    p_logout = sub.add_parser("logout", help="Clear local session", parents=[common])
    p_logout.set_defaults(func=cmd_logout)

    p_who = sub.add_parser("whoami", help="Show current session", parents=[common])
    p_who.set_defaults(func=cmd_whoami)

    p_cp = sub.add_parser("change-password", help="Change password", parents=[common])
    p_cp.add_argument("--old", required=True)
    p_cp.add_argument("--new", required=True)
    p_cp.set_defaults(func=cmd_change_password)

    # record
    p_add = sub.add_parser("add", help="Add a record", parents=[common])
    p_add.add_argument("--type", required=True, choices=[e.name for e in RecordType])
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--amount", required=True, type=float)
    p_add.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_add.add_argument("--note", default="")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List records for a month", parents=[common])
    p_list.add_argument("--month", required=True, help="YYYY-MM")
    p_list.set_defaults(func=cmd_list)

    p_stats = sub.add_parser(
        "stats", help="Show monthly summary/plot", parents=[common]
    )
    p_stats.add_argument("--month", required=True, help="YYYY-MM")
    p_stats.add_argument(
        "--plot", action="store_true", help="Save a category pie chart to reports/"
    )
    p_stats.add_argument(
        "--reports-dir", default="reports", help="Output folder for charts"
    )
    p_stats.set_defaults(func=cmd_stats)

    # budgets
    p_budget = sub.add_parser("budget", help="Manage budgets", parents=[common])
    bsub = p_budget.add_subparsers(dest="bcommand", required=True)

    b_set = bsub.add_parser("set", help="Set/update a budget", parents=[common])
    b_set.add_argument("--category", required=True)
    b_set.add_argument("--limit", required=True, type=float)
    b_set.set_defaults(func=cmd_budget_set)

    b_list = bsub.add_parser("list", help="List budgets", parents=[common])
    b_list.set_defaults(func=cmd_budget_list)

    b_prog = bsub.add_parser("progress", help="Show budget progress", parents=[common])
    b_prog.add_argument("--month", required=True, help="YYYY-MM")
    b_prog.set_defaults(func=cmd_budget_progress)

    # reminders
    p_rem = sub.add_parser("reminder", help="Manage reminders", parents=[common])
    rsub = p_rem.add_subparsers(dest="rcommand", required=True)

    r_set = rsub.add_parser("set", help="Add a reminder", parents=[common])
    r_set.add_argument("--time", required=True, help="HH:MM (24h)")
    r_set.add_argument("--message", required=False, default="记账提醒")
    g = r_set.add_mutually_exclusive_group()
    g.add_argument("--enabled", action="store_true", help="enable (default)")
    g.add_argument("--disable", action="store_true", help="disable")
    r_set.set_defaults(func=cmd_reminder_set)

    r_list = rsub.add_parser("list", help="List reminders", parents=[common])
    r_list.set_defaults(func=cmd_reminder_list)

    r_emit = rsub.add_parser("emit", help="Emit enabled reminders", parents=[common])
    r_emit.set_defaults(func=cmd_reminder_emit)

    # CSV
    p_imp = sub.add_parser(
        "import-csv", help="Import records from CSV", parents=[common]
    )
    p_imp.add_argument("--path", required=True)
    p_imp.set_defaults(func=cmd_import_csv)

    p_exp = sub.add_parser("export-csv", help="Export records to CSV", parents=[common])
    p_exp.add_argument("--path", required=True)
    p_exp.add_argument("--month", required=False, help="YYYY-MM (optional)")
    p_exp.set_defaults(func=cmd_export_csv)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
