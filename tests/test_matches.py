import pytest

from models.games import add_game
from models.matches import (
    check_duration,
    check_player_count,
    count_wins,
    create_match,
    finish_match,
    get_game_status,
    iter_unfinished,
)


def make_games():
    games = {}
    add_game(games, "Каркассон", 2, 5)
    add_game(games, "Шахматы", 2, 2)
    return games


def test_pr1_checks():
    assert check_player_count(1).startswith("ошибка")
    assert check_player_count(7).startswith("ошибка")
    assert check_player_count(4) == "количество игроков корректное."
    assert check_duration(0).startswith("ошибка")
    assert check_duration(300).startswith("предупреждение")
    assert get_game_status(True) == "партия завершена."


def test_create_match():
    matches = []
    match = create_match(matches, make_games(), 1, "2026-09-15", 4, 60)
    assert len(matches) == 1
    assert match["is_completed"] is False


def test_create_match_wrong_players_for_game():
    with pytest.raises(ValueError):
        create_match([], make_games(), 2, "2026-09-15", 4, 60)


def test_finish_match_and_wins():
    matches = []
    create_match(matches, make_games(), 1, "2026-09-15", 3, 60)
    assert finish_match(matches, 1, "Артём")
    assert not finish_match(matches, 1, "Мария")
    assert count_wins(matches) == {"Артём": 1}
    assert list(iter_unfinished(matches)) == []
