"""Сохранение и загрузка данных в JSON-файлах."""

import json
from typing import Dict, List

GAMES_FILE = "data/games.json"
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


def load_games(filename: str = GAMES_FILE) -> Dict[int, dict]:
    """Загрузить игры: список из JSON превращается в словарь по id."""
    return {game["id"]: game for game in _read(filename)}


def save_games(games: Dict[int, dict], filename: str = GAMES_FILE) -> None:
    """Сохранить игры в JSON-файл."""
    _write(filename, list(games.values()))


def load_matches(filename: str = MATCHES_FILE) -> List[dict]:
    """Загрузить партии из JSON-файла."""
    return _read(filename)


def save_matches(matches: List[dict], filename: str = MATCHES_FILE) -> None:
    """Сохранить партии в JSON-файл."""
    _write(filename, matches)
