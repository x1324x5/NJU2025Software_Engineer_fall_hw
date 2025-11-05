import uuid
import sys
from ledger.api import cli


def _run_cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["prog", *argv])
    cli.main()


def test_cli_init_login_add_list_stats(tmp_path, capsys, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/cli_{uuid.uuid4().hex}.db"

    _run_cli(monkeypatch, "init-db", "--db", db_url)
    assert "Initialized database" in capsys.readouterr().out

    uname = f"user_{uuid.uuid4().hex[:8]}"

    _run_cli(
        monkeypatch,
        "register",
        "--db",
        db_url,
        "--username",
        uname,
        "--password",
        "123456",
        "--email",
        f"{uname}@ex.com",
    )
    assert "registered user" in capsys.readouterr().out

    _run_cli(
        monkeypatch,
        "login",
        "--db",
        db_url,
        "--username",
        uname,
        "--password",
        "123456",
    )
    assert "login ok" in capsys.readouterr().out

    _run_cli(
        monkeypatch,
        "add",
        "--db",
        db_url,
        "--type",
        "INCOME",
        "--category",
        "salary",
        "--amount",
        "1000",
        "--date",
        "2025-01-01",
        "--note",
        "monthly",
    )
    assert "added record" in capsys.readouterr().out

    _run_cli(
        monkeypatch,
        "add",
        "--db",
        db_url,
        "--type",
        "EXPENSE",
        "--category",
        "food",
        "--amount",
        "50.5",
        "--date",
        "2025-01-02",
        "--note",
        "lunch",
    )
    assert "added record" in capsys.readouterr().out

    _run_cli(monkeypatch, "list", "--db", db_url, "--month", "2025-01")
    out = capsys.readouterr().out
    assert "RecordType.INCOME" in out and "RecordType.EXPENSE" in out

    _run_cli(monkeypatch, "stats", "--db", db_url, "--month", "2025-01")
    out = capsys.readouterr().out
    assert "Summary for" in out and "income" in out.lower()

    _run_cli(monkeypatch, "logout")
    assert "logged out" in capsys.readouterr().out.lower()
