# Ledger Skeleton

A minimal, testable skeleton for a ledger (bookkeeping) application.

## Quickstart
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate ; Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt

# Run CLI
python -m ledger.api.cli --help

# Run tests
pytest -q
```

## Layout
```text
ledger/
  models/          # Domain entities (User, Record, Budget, Reminder)
  repo/            # Persistence layer (SQLite + CSV I/O)
  services/        # Business logic (statistics, validation, budgets, reminders)
  api/             # CLI (and optional web API later)
  utils/           # Helpers (db connection, common funcs)
data/              # Sample data (CSV)
tests/             # Unit tests
reports/           # Lint/test reports (ignored by Git)
```
