"""Класс Match и функции работы с коллекцией партий (ПР3)."""

from typing import List, Optional

from models.games import Game
from models.players import Player

MIN_PLAYERS = 2
MAX_PLAYERS = 6
LONG_MATCH_MINUTES = 240


def check_player_count(player_count: int) -> str:
    """Проверить количество игроков по общим правилам системы."""
    if player_count < MIN_PLAYERS:
        return f"ошибка: минимум {MIN_PLAYERS} игрока."
    if player_count > MAX_PLAYERS:
        return f"ошибка: максимум {MAX_PLAYERS} игроков."
    return "количество игроков корректное."


def check_duration(duration_minutes: int) -> str:
    """Проверить продолжительность партии."""
    if duration_minutes <= 0:
        return "ошибка: продолжительность должна быть больше нуля."
    if duration_minutes > LONG_MATCH_MINUTES:
        return "предупреждение: партия длится более 4 часов."
    return "продолжительность партии корректная."


def get_game_status(is_completed: bool) -> str:
    """Текстовый статус партии."""
    return "партия завершена." if is_completed else "партия продолжается."


class Match:
    """Партия в настольную игру."""

    def __init__(
        self,
        match_id: int,
        game: Game,
        match_date: str,
        duration_minutes: int,
        players: List[Player],
        winner: Optional[Player] = None,
        is_completed: bool = False,
    ) -> None:
        self.id = match_id
        self.game = game
        self.match_date = match_date
        self.duration_minutes = duration_minutes
        self.players = players
        self.winner = winner
        self.is_completed = is_completed

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def status(self) -> str:
        return get_game_status(self.is_completed)

    @property
    def duration_hours(self) -> float:
        return round(self.duration_minutes / 60, 1)

    def finish(self, winner: Player) -> None:
        """Завершить партию и указать победителя."""
        if winner not in self.players:
            raise ValueError("Победитель должен быть участником партии.")
        self.winner = winner
        self.is_completed = True

    def to_data(self) -> dict:
        return {
            "id": self.id,
            "game_id": self.game.id,
            "match_date": self.match_date,
            "duration_minutes": self.duration_minutes,
            "player_ids": [player.id for player in self.players],
            "winner_id": self.winner.id if self.winner else None,
            "is_completed": self.is_completed,
        }

    def __str__(self) -> str:
        winner = self.winner.name if self.winner else "—"
        return (
            f"[{self.id}] {self.match_date} {self.game.title}: "
            f"{self.player_count} игр., {self.duration_minutes} мин., "
            f"победитель: {winner}, {self.status}"
        )


def create_match(
    matches: List[Match],
    game: Game,
    match_date: str,
    duration_minutes: int,
    players: List[Player],
) -> Match:
    """Проверить данные, создать партию и добавить её в коллекцию."""
    message = check_player_count(len(players))
    if message.startswith("ошибка"):
        raise ValueError(message)
    if not game.is_suitable_for(len(players)):
        raise ValueError(
            f"В «{game.title}» играют от {game.min_players} "
            f"до {game.max_players} человек."
        )
    message = check_duration(duration_minutes)
    if message.startswith("ошибка"):
        raise ValueError(message)
    new_id = max((match.id for match in matches), default=0) + 1
    match = Match(new_id, game, match_date, duration_minutes, list(players))
    matches.append(match)
    return match


def finish_match(
    matches: List[Match],
    match_id: int,
    winner: Player,
) -> Optional[Match]:
    """Найти партию и завершить её."""
    match = find_match_by_id(matches, match_id)
    if match is not None:
        match.finish(winner)
    return match


def find_match_by_id(matches: List[Match], match_id: int) -> Optional[Match]:
    """Найти партию по идентификатору."""
    for match in matches:
        if match.id == match_id:
            return match
    return None


def matches_for_game(matches: List[Match], game: Game) -> List[Match]:
    """Партии по выбранной игре."""
    return [match for match in matches if match.game.id == game.id]


def count_wins(matches: List[Match], player: Player) -> int:
    """Количество побед игрока."""
    return sum(
        1
        for match in matches
        if match.winner is not None and match.winner.id == player.id
    )


def show_matches(matches: List[Match]) -> None:
    """Вывести партии в консоль."""
    if not matches:
        print("Партии не найдены.")
    for match in matches:
        print(match)
