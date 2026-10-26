"""Консольная система учета партий в настольные игры (ПР2)."""

from typing import Dict, Iterable, List

from models.games import (
    check_game_players,
    filter_games_by_players,
    find_game,
    iter_game_lines,
    sort_games,
)
from models.matches import (
    check_duration,
    check_player_count,
    count_wins,
    create_match,
    finish_match,
    get_game_status,
    iter_unfinished,
)
from storage import load_games, load_matches, save_matches
from utils import input_date, input_int

MENU = """
=== Система учета партий в настольные игры ===
1. Показать игры
2. Найти игру по названию
3. Проверить число игроков для игры
4. Подобрать игры по числу игроков
5. Создать партию
6. Завершить партию
7. Показать партии
8. Рейтинг игроков
9. Проверить данные партии (сценарий ПР1)
0. Выход
"""


def show_games(games: Iterable[dict]) -> None:
    """Вывести список игр."""
    for line in iter_game_lines(games):
        print(line)


def show_matches(matches: List[dict], games: Dict[int, dict]) -> None:
    """Вывести список партий с названиями игр."""
    if not matches:
        print("Партий пока нет.")
    for match in matches:
        title = games[match["game_id"]]["title"]
        winner = match["winner"] or "—"
        print(
            f"{match['id']:>3}. {match['match_date']} {title:<18}"
            f"{match['player_count']} игр., {match['duration_minutes']} мин."
            f"  победитель: {winner}  "
            f"({get_game_status(match['is_completed'])})"
        )


def check_match_scenario() -> None:
    """Сценарий ПР1: проверка введённых данных одной партии."""
    player_count = input_int("Количество игроков: ")
    duration = input_int("Продолжительность партии в минутах: ")
    completed = input("Партия завершена? (да/нет): ").lower() == "да"
    print(check_player_count(player_count))
    print(check_duration(duration))
    print(get_game_status(completed))


def create_new_match(matches: List[dict], games: Dict[int, dict]) -> None:
    """Пользовательский сценарий создания партии."""
    show_games(games.values())
    game_id = input_int("Номер игры: ")
    match_date = input_date("Дата (ГГГГ-ММ-ДД, пусто – сегодня): ")
    player_count = input_int("Количество игроков: ")
    duration = input_int("Продолжительность в минутах: ")
    try:
        match = create_match(
            matches, games, game_id, match_date, player_count, duration
        )
    except ValueError as error:
        print(f"Партия не создана: {error}")
        return
    print(f"Партия №{match['id']} создана.")
    print(check_duration(duration))


def main() -> None:
    """Точка запуска: загрузка данных, меню, сохранение."""
    games = load_games()
    matches = load_matches()
    while True:
        print(MENU)
        choice = input("Выберите действие: ").strip()
        if choice == "1":
            show_games(sort_games(games))
        elif choice == "2":
            found = find_game(games, input("Часть названия: "))
            show_games(found)
        elif choice == "3":
            game_id = input_int("Номер игры: ")
            count = input_int("Количество игроков: ")
            if check_game_players(games, game_id, count):
                print("Игра подходит для такого числа игроков.")
            else:
                print("Игра не подходит (или не найдена).")
        elif choice == "4":
            count = input_int("Количество игроков: ")
            found = filter_games_by_players(games, count)
            show_games(found)
        elif choice == "5":
            create_new_match(matches, games)
            save_matches(matches)
        elif choice == "6":
            unfinished = list(iter_unfinished(matches))
            show_matches(unfinished, games)
            match_id = input_int("Номер партии: ")
            winner = input("Имя победителя: ").strip()
            if winner and finish_match(matches, match_id, winner):
                save_matches(matches)
                print("Партия завершена.")
            else:
                print("Не удалось завершить партию.")
        elif choice == "7":
            show_matches(matches, games)
        elif choice == "8":
            ranking = sorted(
                count_wins(matches).items(),
                key=lambda pair: pair[1],
                reverse=True,
            )
            for name, wins in ranking:
                print(f"{name}: {wins}")
        elif choice == "9":
            check_match_scenario()
        elif choice == "0":
            save_matches(matches)
            print("До свидания!")
            break
        else:
            print("Неизвестный пункт меню.")


if __name__ == "__main__":
    main()
