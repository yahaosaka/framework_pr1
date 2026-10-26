import re
import sqlite3
from pathlib import Path

import pytest

from db import import_json
from db.database import fetch_all, fetch_one, get_connection

QUERIES = Path(__file__).resolve().parent.parent / "sql" / "queries.sql"


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.sqlite"
    import_json.main(path)
    return path


def test_tables_and_counts(db_path):
    conn = get_connection(db_path)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"games", "players", "matches", "match_players"} <= tables
    games = import_json.load_json(import_json.GAMES_FILE)
    count = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert count == len(games)
    conn.close()


def test_import_is_repeatable(db_path):
    import_json.main(db_path)
    row = fetch_one("SELECT COUNT(*) AS n FROM players", db_path=db_path)
    assert row["n"] == len(import_json.load_json(import_json.PLAYERS_FILE))


def test_foreign_keys_enforced(db_path):
    conn = get_connection(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO matches (game_id, match_date, duration_minutes) "
            "VALUES (?, ?, ?)",
            (999, "2026-10-01", 30),
        )
    conn.close()


def test_parameterized_search(db_path):
    rows = fetch_all(
        "SELECT title FROM games WHERE min_players <= ? AND max_players >= ?",
        [6, 6],
        db_path=db_path,
    )
    assert all(row["title"] for row in rows)
    injected = fetch_all(
        "SELECT title FROM games WHERE title = ?",
        ["' OR 1=1 --"],
        db_path=db_path,
    )
    assert injected == []


def test_all_queries_run(db_path):
    text = QUERIES.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=-- \d+\.)", text)[1:]
    assert len(blocks) >= 10
    conn = get_connection(db_path)
    for block in blocks:
        sql = "\n".join(
            line for line in block.splitlines()
            if not line.strip().startswith("--")
        )
        conn.execute(sql).fetchall()
    conn.close()
