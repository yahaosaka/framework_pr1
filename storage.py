"""Загрузка и сохранение данных: JSON ↔ объекты классов (ПР3)."""

import json
from typing import List

from models.games import Game, find_game_by_id
from models.matches import Match
from models.players import Player, find_player_by_id

GAMES_FILE = "data/games.json"
PLAYERS_FILE = "data/players.json"
MATCHES_FILE = "data/matches.json"


def _read(filename: str) -> list:
    """Прочитать список из JSON-файла; ошибки файла не прерывают работу."""
    try:
        with open(filename, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Файл {filename} не найден, начинаем с пустых данных.")
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, начинаем с пустых данных.")
    return []


def _write(filename: str, data: list) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_games(filename: str = GAMES_FILE) -> List[Game]:
    """JSON → объекты Game."""
    return [Game.from_data(item) for item in _read(filename)]


def save_games(games: List[Game], filename: str = GAMES_FILE) -> None:
    """Объекты Game → JSON."""
    _write(filename, [game.to_data() for game in games])


def load_players(filename: str = PLAYERS_FILE) -> List[Player]:
    """JSON → объекты Player."""
    return [Player.from_data(item) for item in _read(filename)]


def save_players(players: List[Player], filename: str = PLAYERS_FILE) -> None:
    """Объекты Player → JSON."""
    _write(filename, [player.to_data() for player in players])


def load_matches(
    filename: str,
    games: List[Game],
    players: List[Player],
) -> List[Match]:
    """JSON → объекты Match со ссылками на объекты Game и Player."""
    matches = []
    for item in _read(filename):
        game = find_game_by_id(games, item["game_id"])
        if game is None:
            continue
        participants = [
            find_player_by_id(players, player_id)
            for player_id in item["player_ids"]
        ]
        participants = [player for player in participants if player]
        winner = None
        if item.get("winner_id") is not None:
            winner = find_player_by_id(players, item["winner_id"])
        matches.append(
            Match(
                item["id"],
                game,
                item["match_date"],
                item["duration_minutes"],
                participants,
                winner,
                item.get("is_completed", False),
            )
        )
    return matches


def save_matches(matches: List[Match], filename: str = MATCHES_FILE) -> None:
    """Объекты Match → JSON (связи сохраняются идентификаторами)."""
    _write(filename, [match.to_data() for match in matches])
