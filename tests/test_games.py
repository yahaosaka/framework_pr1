import pytest

from models.games import (
    add_game,
    check_game_players,
    filter_games_by_players,
    find_game,
    sort_games,
)


def make_games():
    games = {}
    add_game(games, "Каркассон", 2, 5, "стратегия")
    add_game(games, "Шахматы", 2, 2, "классика")
    add_game(games, "Диксит", 3, 6, "ассоциации")
    return games


def test_add_game():
    games = {}
    game = add_game(games, "Монополия", 2, 6)
    assert len(games) == 1
    assert game["id"] == 1


def test_add_game_wrong_players():
    with pytest.raises(ValueError):
        add_game({}, "Игра", 5, 2)


def test_find_game_ignores_case():
    assert find_game(make_games(), "шах")[0]["title"] == "Шахматы"


def test_check_game_players():
    games = make_games()
    assert check_game_players(games, 1, 4)
    assert not check_game_players(games, 2, 3)
    assert not check_game_players(games, 99, 3)


def test_filter_and_sort():
    games = make_games()
    titles = [g["title"] for g in filter_games_by_players(games, 2)]
    assert titles == ["Каркассон", "Шахматы"]
    ordered = sort_games(games)
    assert ordered[0]["title"] == "Диксит"
