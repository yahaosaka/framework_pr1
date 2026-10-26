"""Работа с настольными играми (данные хранятся в словаре games)."""

from typing import Dict, Iterable, Iterator, List

MIN_PLAYERS = 2
MAX_PLAYERS = 6


def add_game(
    games: Dict[int, dict],
    title: str,
    min_players: int,
    max_players: int,
    genre: str = "",
) -> dict:
    """Добавить игру в словарь games и вернуть её данные.

    Идентификатор формируется как максимальный существующий + 1.
    """
    if not title.strip():
        raise ValueError("Название игры не может быть пустым.")
    if not MIN_PLAYERS <= min_players <= max_players <= MAX_PLAYERS:
        raise ValueError(
            f"Число игроков должно быть от {MIN_PLAYERS} до {MAX_PLAYERS}."
        )
    game_id = max(games, default=0) + 1
    games[game_id] = {
        "id": game_id,
        "title": title.strip(),
        "min_players": min_players,
        "max_players": max_players,
        "genre": genre,
    }
    return games[game_id]


def find_game(games: Dict[int, dict], query: str) -> List[dict]:
    """Найти игры по подстроке названия (без учета регистра)."""
    query = query.lower()
    found = []
    for game in games.values():
        if query in game["title"].lower():
            found.append(game)
    return found


def check_game_players(
    games: Dict[int, dict],
    game_id: int,
    player_count: int,
) -> bool:
    """Проверить, подходит ли игра для заданного числа игроков."""
    game = games.get(game_id)
    if game is None:
        return False
    return game["min_players"] <= player_count <= game["max_players"]


def filter_games_by_players(
    games: Dict[int, dict],
    player_count: int,
) -> List[dict]:
    """Отобрать игры, в которые можно играть вдвоём, втроём и т. д."""
    return [
        game
        for game in games.values()
        if game["min_players"] <= player_count <= game["max_players"]
    ]


def sort_games(games: Dict[int, dict], by: str = "title") -> List[dict]:
    """Отсортировать игры по названию или по максимуму игроков."""
    if by == "players":
        return sorted(
            games.values(),
            key=lambda game: game["max_players"],
            reverse=True,
        )
    return sorted(games.values(), key=lambda game: game["title"])


def iter_game_lines(games: Iterable[dict]) -> Iterator[str]:
    """Генератор строк для вывода списка игр."""
    for game in games:
        yield (
            f"{game['id']:>3}. {game['title']:<22}"
            f"{game['min_players']}-{game['max_players']} игр.  "
            f"{game['genre']}"
        )
