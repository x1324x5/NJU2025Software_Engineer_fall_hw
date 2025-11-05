"""SQLAlchemy table schema (Core) for SQLite backing store."""

from __future__ import annotations
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    Date,
    Time,
    Boolean,
    ForeignKey,
)

metadata = MetaData()


users = Table(
    "users",
    metadata,
    Column("user_id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False, unique=True),
    Column("email", String(255), nullable=True),
    Column("password_hash", String(128), nullable=False),  # ← 新增：存密码散列
)

records = Table(
    "records",
    metadata,
    Column("record_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), nullable=False, index=True),
    Column("rtype", String(10), nullable=False),  # INCOME / EXPENSE
    Column("category", String(100), nullable=False, index=True),
    Column("amount", Float, nullable=False),
    Column("occurred_on", Date, nullable=False, index=True),
    Column("note", String(500), nullable=False, default=""),
)

budgets = Table(
    "budgets",
    metadata,
    Column("budget_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), nullable=False, index=True),
    Column("category", String(100), nullable=False, index=True),
    Column("monthly_limit", Float, nullable=False),
)

reminders = Table(
    "reminders",
    metadata,
    Column("reminder_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), nullable=False, index=True),
    Column("message", String(255), nullable=False),
    Column("at", Time, nullable=False),
    Column("enabled", Boolean, nullable=False, default=True),
)
