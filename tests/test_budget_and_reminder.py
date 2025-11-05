import uuid
import sys
from ledger.api import cli


def _run_cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["prog", *argv])
    cli.main()


def test_budget_progress_and_reminders_via_cli(tmp_path, capsys, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/br_{uuid.uuid4().hex}.db"

    # 初始化 + 注册 + 登录
    _run_cli(monkeypatch, "init-db", "--db", db_url)
    capsys.readouterr()

    _run_cli(
        monkeypatch,
        "register",
        "--db",
        db_url,
        "--username",
        "bob",
        "--password",
        "123456",
        "--email",
        "b@example.com",
    )
    capsys.readouterr()

    _run_cli(
        monkeypatch,
        "login",
        "--db",
        db_url,
        "--username",
        "bob",
        "--password",
        "123456",
    )
    capsys.readouterr()

    # 添加几条 2025-01 的支出，便于预算进度计算
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
        "30",
        "--date",
        "2025-01-05",
        "--note",
        "breakfast",
    )
    capsys.readouterr()
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
        "20",
        "--date",
        "2025-01-06",
        "--note",
        "lunch",
    )
    capsys.readouterr()

    # 预算：set / list / progress（注意：你的表结构没有 period 字段）
    _run_cli(
        monkeypatch,
        "budget",
        "set",
        "--db",
        db_url,
        "--category",
        "food",
        "--limit",
        "100",
    )
    out = capsys.readouterr().out
    assert "budget set" in out.lower()

    _run_cli(monkeypatch, "budget", "list", "--db", db_url)
    out = capsys.readouterr().out
    assert "food" in out and "100.0" in out

    _run_cli(monkeypatch, "budget", "progress", "--db", db_url, "--month", "2025-01")
    out = capsys.readouterr().out
    # 输出类似： "Budget progress for bob 2025-01\n  food: XX.X%"
    assert "Budget progress for bob 2025-01" in out
    assert "food:" in out

    # 提醒：set / list / emit（你的 Reminder 无 frequency 字段）
    _run_cli(
        monkeypatch,
        "reminder",
        "set",
        "--db",
        db_url,
        "--time",
        "09:00",
        "--message",
        "记账一下",
    )
    out = capsys.readouterr().out
    assert "reminder added" in out.lower()

    _run_cli(monkeypatch, "reminder", "list", "--db", db_url)
    out = capsys.readouterr().out
    assert "09:00:00" in out and "ON" in out

    _run_cli(monkeypatch, "reminder", "emit", "--db", db_url)
    out = capsys.readouterr().out
    # emit 的每条输出为：[reminder] 09:00:00 - 记账一下
    assert "[reminder] 09:00:00 - 记账一下" in out

    # 登出
    _run_cli(monkeypatch, "logout")
    out = capsys.readouterr().out
    assert "logged out" in out.lower()
