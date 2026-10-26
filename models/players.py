"""Класс Player и функции работы с коллекцией игроков (ПР3)."""

from typing import List, Optional


class Player:
    """Участник партий."""

    def __init__(
        self,
        player_id: int,
        name: str,
        email: str = "",
    ) -> None:
        self.id = player_id
        self.name = name
        self.email = email

    def to_data(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email}

    @classmethod
    def from_data(cls, data: dict) -> "Player":
        return cls(data["id"], data["name"], data.get("email", ""))

    def __str__(self) -> str:
        return f"[{self.id}] {self.name}"


def add_player(players: List[Player], name: str, email: str = "") -> Player:
    """Создать игрока и добавить его в коллекцию."""
    if not name.strip():
        raise ValueError("Имя игрока не может быть пустым.")
    new_id = max((player.id for player in players), default=0) + 1
    player = Player(new_id, name.strip(), email.strip())
    players.append(player)
    return player


def find_player(players: List[Player], text: str) -> List[Player]:
    """Найти игроков по части имени или адресу почты."""
    text = text.lower()
    return [
        player
        for player in players
        if text in player.name.lower() or text in player.email.lower()
    ]


def find_player_by_id(
    players: List[Player],
    player_id: int,
) -> Optional[Player]:
    """Найти игрока по идентификатору."""
    for player in players:
        if player.id == player_id:
            return player
    return None


def show_players(players: List[Player]) -> None:
    """Вывести игроков в консоль."""
    if not players:
        print("Игроки не найдены.")
    for player in players:
        print(player)
