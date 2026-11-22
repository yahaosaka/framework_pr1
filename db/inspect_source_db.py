"""Инспекция исходной базы без изменения файла."""
import sqlite3
from contextlib import closing
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "data" / "boardgames.sqlite"


def main():
    with closing(sqlite3.connect(
            SOURCE.as_uri() + "?mode=ro", uri=True)) as conn:
        for table in ("games", "players", "matches", "match_players"):
            columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print(table, "rows:", count)
            for column in columns:
                print(" ", column)
        print("Foreign key errors:",
              conn.execute("PRAGMA foreign_key_check").fetchall())


if __name__ == "__main__":
    main()
