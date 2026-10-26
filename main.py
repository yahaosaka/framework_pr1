"""Консольная система учета партий в настольные игры (ПР3, ООП)."""

from typing import List

from models import Game, Match, Player
from models.games import (
    add_game,
    check_game_players,
    filter_games_by_players,
    find_game,
    find_game_by_id,
    show_games,
    sort_games,
)
from models.matches import (
    check_duration,
    check_player_count,
    count_wins,
    create_match,
    finish_match,
    get_game_status,
    show_matches,
)
from models.players import (
    add_player,
    find_player,
    find_player_by_id,
    show_players,
)
from storage import (
    GAMES_FILE,
    MATCHES_FILE,
    PLAYERS_FILE,
    load_games,
    load_matches,
    load_players,
    save_games,
    save_matches,
    save_players,
)
from utils import input_date, input_int

MENU = """
==============================================
 СИСТЕМА УЧЕТА ПАРТИЙ В НАСТОЛЬНЫЕ ИГРЫ
==============================================
1. Показать игры
2. Добавить игру
3. Найти игру по названию
4. Игры для заданного числа игроков
5. Проверить, подходит ли игра для числа игроков
6. Показать игроков
7. Добавить игрока
8. Найти игрока
9. Показать партии
10. Создать партию
11. Завершить партию
12. Рейтинг игроков
13. Проверить данные партии (сценарий ПР1)
0. Выход
"""


def choose_players(players: List[Player]) -> List[Player]:
    """Выбрать участников партии по идентификаторам."""
    show_players(players)
    chosen: List[Player] = []
    for value in input("id участников через пробел: ").split():
        if not value.isdigit():
            continue
        player = find_player_by_id(players, int(value))
        if player is not None and player not in chosen:
            chosen.append(player)
    return chosen


def add_new_game(games: List[Game]) -> None:
    """Сценарий добавления игры."""
    title = input("Название: ")
    min_players = input_int("Минимум игроков: ", 2, 6)
    max_players = input_int("Максимум игроков: ", min_players, 6)
    genre = input("Жанр: ")
    game = add_game(games, title, min_players, max_players, genre)
    print("Добавлена:", game)


def create_new_match(
    matches: List[Match],
    games: List[Game],
    players: List[Player],
) -> None:
    """Сценарий создания партии: игра, дата, участники."""
    show_games(games)
    game = find_game_by_id(games, input_int("id игры: "))
    if game is None:
        print("Игра не найдена.")
        return
    match_date = input_date("Дата (ГГГГ-ММ-ДД, пусто – сегодня): ")
    duration = input_int("Продолжительность, мин: ")
    print(check_duration(duration))
    participants = choose_players(players)
    match = create_match(matches, game, match_date, duration, participants)
    print("Создана:", match)


def finish_selected_match(
    matches: List[Match],
    players: List[Player],
) -> None:
    """Сценарий завершения партии с выбором победителя."""
    show_matches(matches)
    match_id = input_int("id партии: ")
    winner = find_player_by_id(players, input_int("id победителя: "))
    if winner is None:
        print("Игрок не найден.")
    elif finish_match(matches, match_id, winner) is None:
        print("Партия не найдена.")
    else:
        print("Партия завершена.")


def show_rating(matches: List[Match], players: List[Player]) -> None:
    """Вывести игроков по числу побед."""
    rating = sorted(
        players,
        key=lambda player: count_wins(matches, player),
        reverse=True,
    )
    for player in rating:
        print(f"{player.name}: побед – {count_wins(matches, player)}")


def check_match_scenario() -> None:
    """Сценарий ПР1: проверка введённых данных одной партии."""
    player_count = input_int("Количество игроков: ")
    duration = input_int("Продолжительность партии в минутах: ")
    completed = input("Партия завершена? (да/нет): ").lower() == "да"
    print(check_player_count(player_count))
    print(check_duration(duration))
    print(get_game_status(completed))


def main() -> None:
    """Загрузить данные, запустить меню и сохранить изменения."""
    games = load_games(GAMES_FILE)
    players = load_players(PLAYERS_FILE)
    matches = load_matches(MATCHES_FILE, games, players)

    while True:
        print(MENU)
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "1":
                show_games(sort_games(games))
            elif choice == "2":
                add_new_game(games)
            elif choice == "3":
                show_games(find_game(games, input("Часть названия: ")))
            elif choice == "4":
                count = input_int("Сколько игроков: ", 1)
                show_games(filter_games_by_players(games, count))
            elif choice == "5":
                game_id = input_int("id игры: ")
                count = input_int("Сколько игроков: ", 1)
                if check_game_players(games, game_id, count):
                    print("Игра подходит.")
                else:
                    print("Игра не подходит (или не найдена).")
            elif choice == "6":
                show_players(players)
            elif choice == "7":
                player = add_player(players, input("Имя: "), input("Email: "))
                print("Добавлен:", player)
            elif choice == "8":
                show_players(find_player(players, input("Имя или email: ")))
            elif choice == "9":
                show_matches(matches)
            elif choice == "10":
                create_new_match(matches, games, players)
            elif choice == "11":
                finish_selected_match(matches, players)
            elif choice == "12":
                show_rating(matches, players)
            elif choice == "13":
                check_match_scenario()
            elif choice == "0":
                save_games(games, GAMES_FILE)
                save_players(players, PLAYERS_FILE)
                save_matches(matches, MATCHES_FILE)
                print("Данные сохранены. До свидания!")
                break
            else:
                print("Нет такого пункта.")
        except ValueError as error:
            print("Ошибка:", error)


if __name__ == "__main__":
    main()
