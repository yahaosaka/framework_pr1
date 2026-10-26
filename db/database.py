"""Подключение к базе данных SQLite."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "boardgames.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path=DB_PATH):
    """Открыть соединение и включить проверку внешних ключей."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(db_path=DB_PATH):
    """Выполнить sql/schema.sql (повторный запуск безопасен)."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def fetch_all(sql, params=(), db_path=DB_PATH):
    """Выполнить SELECT и вернуть все строки (доступ к полям по именам)."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=(), db_path=DB_PATH):
    """Выполнить SELECT и вернуть одну строку или None."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()
