"""Ledger CLI: add/list/stats/import/export/init-db.
Usage examples:
  python -m ledger.api.cli init-db --db ./ledger.db
  python -m ledger.api.cli add --user alice --type EXPENSE --category food --amount 25.5 --date 2025-01-02 --note lunch
  python -m ledger.api.cli list --user alice --month 2025-01
  python -m ledger.api.cli stats --user alice --month 2025-01 --plot
  python -m ledger.api.cli import-csv --user alice --path data/sample_records.csv
  python -m ledger.api.cli export-csv --user alice --path reports/export.csv --month 2025-01
"""

from __future__ import annotations
import argparse
from pathlib import Path
from datetime import date, datetime
from typing import Iterable, List, Tuple
import matplotlib.pyplot as plt

from ..utils.db import init_db, get_session_factory
from ..repo.sqlite_user_repo import SqliteUserRepository
from ..repo.sqlite_record_repo import SqliteRecordRepository
from ..models import Record, RecordType, User
from ..services.statistics_service import StatisticsService
from ..services.record_service import RecordService
from ..utils.csv_io import load_records_from_csv, save_records_to_csv


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


def _get_or_create_user(session, name: str) -> User:
    urepo = SqliteUserRepository(session)
    user = urepo.get_by_name(name)
    if user is None:
        user = urepo.add(User(None, name, None))
    return user


def cmd_init_db(args: argparse.Namespace) -> None:
    init_db(db_url=args.db)
    print(f"Initialized database at {args.db}")


def cmd_add(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    user = _get_or_create_user(session, args.user)
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
        f"added record #{created.record_id}: {created.rtype} {created.category} {created.amount} on {created.occurred_on.isoformat()}"
    )


def _iter_month_records(
    session, user_name: str, year: int, month: int
) -> Iterable[Record]:
    user = _get_or_create_user(session, user_name)
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    return svc.list_month(user.user_id, year, month)


def cmd_list(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    year, month = _parse_month(args.month)
    recs = list(_iter_month_records(session, args.user, year, month))
    if not recs:
        print("no records")
        return
    for r in recs:
        print(
            f"#{r.record_id}\t{r.occurred_on.isoformat()}\t{r.rtype}\t{r.category}\t{r.amount:.2f}\t{r.note}"
        )


def cmd_stats(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    year, month = _parse_month(args.month)
    recs = list(_iter_month_records(session, args.user, year, month))
    svc = StatisticsService()
    summary = svc.monthly_summary(recs)
    by_cat = svc.by_category(recs)

    print(f"Summary for {args.user} {year}-{month:02d}")
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
        # Pie chart (categories of expenses)
        labels = list(by_cat.keys())
        values = list(by_cat.values())
        if values:
            import matplotlib.pyplot as plt  # ensure available in function scope

            plt.figure()
            plt.pie(
                values, labels=labels, autopct="%1.1f%%"
            )  # do not set colors explicitly
            out = reports_dir / f"expenses_by_category_{year}-{month:02d}.png"
            plt.title(f"Expenses by Category {year}-{month:02d}")
            plt.savefig(out, bbox_inches="tight")
            plt.close()
            print(f"saved plot: {out}")


def cmd_import_csv(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    user = _get_or_create_user(session, args.user)
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    records = load_records_from_csv(args.path)
    count = 0
    for r in records:
        # ensure user_id is bound to the target user
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
    print(f"imported {count} records for user {args.user}")


def cmd_export_csv(args: argparse.Namespace) -> None:
    session = _get_session(args.db)
    year, month = _parse_month(args.month) if args.month else (None, None)
    user = _get_or_create_user(session, args.user)
    repo = SqliteRecordRepository(session)
    svc = RecordService(repo)
    if year and month:
        recs = list(svc.list_month(user.user_id, year, month))
    else:
        # fall back to a very wide range
        recs = list(
            repo.list_by_period(user.user_id, date(1900, 1, 1), date(3000, 1, 1))
        )
    Path(args.path).parent.mkdir(parents=True, exist_ok=True)
    save_records_to_csv(args.path, recs)
    print(f"exported {len(recs)} records to {args.path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ledger CLI")
    parser.add_argument(
        "--db",
        default="sqlite:///./ledger.db",
        help="SQLAlchemy DB URL (default sqlite:///./ledger.db)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-db", help="Create tables if not exist")
    p_init.set_defaults(func=cmd_init_db)

    p_add = sub.add_parser("add", help="Add a record")
    p_add.add_argument("--user", required=True)
    p_add.add_argument("--type", required=True, choices=[e.name for e in RecordType])
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--amount", required=True, type=float)
    p_add.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_add.add_argument("--note", default="")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List records for a month")
    p_list.add_argument("--user", required=True)
    p_list.add_argument("--month", required=True, help="YYYY-MM")
    p_list.set_defaults(func=cmd_list)

    p_stats = sub.add_parser("stats", help="Show monthly summary and (optionally) plot")
    p_stats.add_argument("--user", required=True)
    p_stats.add_argument("--month", required=True, help="YYYY-MM")
    p_stats.add_argument(
        "--plot", action="store_true", help="Save a category pie chart under reports/"
    )
    p_stats.add_argument(
        "--reports-dir", default="reports", help="Output folder for charts"
    )
    p_stats.set_defaults(func=cmd_stats)

    p_imp = sub.add_parser("import-csv", help="Import records from CSV into a user")
    p_imp.add_argument("--user", required=True)
    p_imp.add_argument("--path", required=True)
    p_imp.set_defaults(func=cmd_import_csv)

    p_exp = sub.add_parser(
        "export-csv", help="Export records to CSV (optionally for a month)"
    )
    p_exp.add_argument("--user", required=True)
    p_exp.add_argument("--path", required=True)
    p_exp.add_argument("--month", required=False, help="YYYY-MM (optional) ")
    p_exp.set_defaults(func=cmd_export_csv)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
