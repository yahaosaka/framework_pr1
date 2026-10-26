"""Перенос данных из JSON-файлов в базу SQLite.

Запуск из корня проекта: python -m db.import_json
"""

import json

from db.database import BASE_DIR, DB_PATH, create_schema, get_connection

GAMES_FILE = BASE_DIR / "data" / "games.json"
PLAYERS_FILE = BASE_DIR / "data" / "players.json"
MATCHES_FILE = BASE_DIR / "data" / "matches.json"


def load_json(filename):
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn):
    """Очистить таблицы (дочерние раньше родительских)."""
    conn.execute("DELETE FROM match_players")
    conn.execute("DELETE FROM matches")
    conn.execute("DELETE FROM players")
    conn.execute("DELETE FROM games")


def import_games(conn, games):
    conn.executemany(
        """
        INSERT INTO games (id, title, min_players, max_players, genre)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                game["id"],
                game["title"],
                game["min_players"],
                game["max_players"],
                game.get("genre"),
            )
            for game in games
        ],
    )


def import_players(conn, players):
    conn.executemany(
        "INSERT INTO players (id, name, email) VALUES (?, ?, ?)",
        [
            (player["id"], player["name"], player.get("email"))
            for player in players
        ],
    )


def import_matches(conn, matches):
    conn.executemany(
        """
        INSERT INTO matches (
            id, game_id, match_date, duration_minutes, winner_id, is_completed
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                match["id"],
                match["game_id"],
                match["match_date"],
                match["duration_minutes"],
                match.get("winner_id"),
                int(match["is_completed"]),
            )
            for match in matches
        ],
    )
    conn.executemany(
        "INSERT INTO match_players (match_id, player_id) VALUES (?, ?)",
        [
            (match["id"], player_id)
            for match in matches
            for player_id in match["player_ids"]
        ],
    )


def main(db_path=DB_PATH):
    create_schema(db_path)
    conn = get_connection(db_path)
    try:
        clear_tables(conn)
        # порядок важен: сначала таблицы, на которые ссылаются внешние ключи
        import_games(conn, load_json(GAMES_FILE))
        import_players(conn, load_json(PLAYERS_FILE))
        import_matches(conn, load_json(MATCHES_FILE))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
    print(f"Данные перенесены в {DB_PATH}")
