"""Класс Game и функции работы с коллекцией игр (ПР3)."""

from typing import List, Optional

MIN_PLAYERS = 2
MAX_PLAYERS = 6


class Game:
    """Настольная игра."""

    def __init__(
        self,
        game_id: int,
        title: str,
        min_players: int,
        max_players: int,
        genre: str = "",
    ) -> None:
        self.id = game_id
        self.title = title
        self.min_players = min_players
        self.max_players = max_players
        self.genre = genre

    def is_suitable_for(self, player_count: int) -> bool:
        """Подходит ли игра для заданного количества игроков."""
        return self.min_players <= player_count <= self.max_players

    @staticmethod
    def validate_players(min_players: int, max_players: int) -> bool:
        """Проверить корректность диапазона числа игроков."""
        return MIN_PLAYERS <= min_players <= max_players <= MAX_PLAYERS

    @property
    def info(self) -> str:
        """Краткое описание игры для отображения."""
        return (
            f"{self.title} ({self.genre}), "
            f"{self.min_players}–{self.max_players} игроков"
        )

    def to_data(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "min_players": self.min_players,
            "max_players": self.max_players,
            "genre": self.genre,
        }

    @classmethod
    def from_data(cls, data: dict) -> "Game":
        return cls(
            data["id"],
            data["title"],
            data["min_players"],
            data["max_players"],
            data.get("genre", ""),
        )

    def __str__(self) -> str:
        return f"[{self.id}] {self.info}"


def add_game(
    games: List[Game],
    title: str,
    min_players: int,
    max_players: int,
    genre: str = "",
) -> Game:
    """Создать игру и добавить её в коллекцию."""
    if not title.strip():
        raise ValueError("Название игры не может быть пустым.")
    if not Game.validate_players(min_players, max_players):
        raise ValueError(
            f"Число игроков должно быть от {MIN_PLAYERS} до {MAX_PLAYERS}."
        )
    new_id = max((game.id for game in games), default=0) + 1
    game = Game(new_id, title.strip(), min_players, max_players, genre)
    games.append(game)
    return game


def find_game(games: List[Game], text: str) -> List[Game]:
    """Найти игры по части названия."""
    text = text.lower()
    return [game for game in games if text in game.title.lower()]


def find_game_by_id(games: List[Game], game_id: int) -> Optional[Game]:
    """Найти игру по идентификатору."""
    for game in games:
        if game.id == game_id:
            return game
    return None


def check_game_players(
    games: List[Game],
    game_id: int,
    player_count: int,
) -> bool:
    """Найти игру и проверить, подходит ли она для числа игроков."""
    game = find_game_by_id(games, game_id)
    return game is not None and game.is_suitable_for(player_count)


def filter_games_by_players(
    games: List[Game],
    player_count: int,
) -> List[Game]:
    """Отобрать игры, подходящие для заданного количества игроков."""
    return [game for game in games if game.is_suitable_for(player_count)]


def sort_games(games: List[Game], by: str = "title") -> List[Game]:
    """Отсортировать игры по названию или максимальному числу игроков."""
    if by == "players":
        return sorted(games, key=lambda game: game.max_players, reverse=True)
    return sorted(games, key=lambda game: game.title)


def show_games(games: List[Game]) -> None:
    """Вывести игры в консоль."""
    if not games:
        print("Игры не найдены.")
    for game in games:
        print(game)
