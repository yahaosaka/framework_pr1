"""Работа с партиями (данные хранятся в списке словарей matches)."""

from typing import Dict, Iterator, List, Optional

from models.games import check_game_players

LONG_MATCH_MINUTES = 240


def check_player_count(player_count: int) -> str:
    """Проверить количество игроков (функция из ПР1)."""
    if player_count < 2:
        return "ошибка: минимум 2 игрока."
    elif player_count > 6:
        return "ошибка: максимум 6 игроков."
    else:
        return "количество игроков корректное."


def check_duration(duration_minutes: int) -> str:
    """Проверить продолжительность партии (функция из ПР1)."""
    if duration_minutes <= 0:
        return "ошибка: продолжительность должна быть больше нуля."
    elif duration_minutes > LONG_MATCH_MINUTES:
        return "предупреждение: партия длится более 4 часов."
    else:
        return "продолжительность партии корректная."


def get_game_status(is_completed: bool) -> str:
    """Вернуть текстовый статус партии (функция из ПР1)."""
    if is_completed:
        return "партия завершена."
    else:
        return "партия продолжается."


def create_match(
    matches: List[dict],
    games: Dict[int, dict],
    game_id: int,
    match_date: str,
    player_count: int,
    duration_minutes: int,
) -> dict:
    """Проверить данные, создать партию и добавить её в список matches."""
    if game_id not in games:
        raise ValueError("Игра с таким номером не найдена.")
    if check_player_count(player_count).startswith("ошибка"):
        raise ValueError(check_player_count(player_count))
    if not check_game_players(games, game_id, player_count):
        raise ValueError("Игра не рассчитана на такое число игроков.")
    if check_duration(duration_minutes).startswith("ошибка"):
        raise ValueError(check_duration(duration_minutes))
    match_id = max((match["id"] for match in matches), default=0) + 1
    match = {
        "id": match_id,
        "game_id": game_id,
        "match_date": match_date,
        "player_count": player_count,
        "duration_minutes": duration_minutes,
        "winner": "",
        "is_completed": False,
    }
    matches.append(match)
    return match


def find_match(matches: List[dict], match_id: int) -> Optional[dict]:
    """Найти партию по идентификатору."""
    for match in matches:
        if match["id"] == match_id:
            return match
    return None


def finish_match(matches: List[dict], match_id: int, winner: str) -> bool:
    """Завершить партию и записать победителя."""
    match = find_match(matches, match_id)
    if match is None or match["is_completed"]:
        return False
    match["winner"] = winner
    match["is_completed"] = True
    return True


def count_wins(matches: List[dict]) -> Dict[str, int]:
    """Подсчитать победы игроков: имя → количество побед."""
    wins: Dict[str, int] = {}
    for match in matches:
        if match["is_completed"] and match["winner"]:
            wins[match["winner"]] = wins.get(match["winner"], 0) + 1
    return wins


def iter_unfinished(matches: List[dict]) -> Iterator[dict]:
    """Генератор незавершённых партий."""
    for match in matches:
        if not match["is_completed"]:
            yield match
