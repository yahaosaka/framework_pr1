import pytest

from models.games import Game
from models.matches import (
    Match,
    check_duration,
    check_player_count,
    count_wins,
    create_match,
    find_match_by_id,
    finish_match,
    get_game_status,
    matches_for_game,
)
from models.players import Player


@pytest.fixture
def data():
    game = Game(1, "Каркассон", 2, 5)
    players = [Player(1, "Анна"), Player(2, "Борис"), Player(3, "Вика")]
    return game, players


def test_check_player_count():
    assert check_player_count(1).startswith("ошибка")
    assert check_player_count(7).startswith("ошибка")
    assert check_player_count(4) == "количество игроков корректное."


def test_match_links_objects(data):
    game, players = data
    match = Match(1, game, "2026-10-01", 90, players)
    assert match.game is game
    assert match.players[0] is players[0]
    assert match.player_count == 3
    assert match.duration_hours == 1.5
    assert match.winner is None


def test_to_data_keeps_only_ids(data):
    game, players = data
    match = Match(1, game, "2026-10-01", 90, players[:2], players[0], True)
    assert match.to_data() == {
        "id": 1,
        "game_id": 1,
        "match_date": "2026-10-01",
        "duration_minutes": 90,
        "player_ids": [1, 2],
        "winner_id": 1,
        "is_completed": True,
    }


def test_check_duration():
    assert check_duration(0).startswith("ошибка")
    assert check_duration(300).startswith("предупреждение")
    assert check_duration(60) == "продолжительность партии корректная."


def test_status():
    assert get_game_status(True) == "партия завершена."
    assert get_game_status(False) == "партия продолжается."


def test_create_and_finish(data):
    game, players = data
    matches = []
    match = create_match(matches, game, "2026-10-01", 60, players[:2])
    assert match.id == 1 and not match.is_completed
    finish_match(matches, 1, players[1])
    assert match.is_completed and match.winner is players[1]
    assert count_wins(matches, players[1]) == 1


def test_create_validation(data):
    game, players = data
    with pytest.raises(ValueError):
        create_match([], game, "2026-10-01", 60, players[:1])
    with pytest.raises(ValueError):
        create_match([], game, "2026-10-01", 0, players)


def test_winner_must_play(data):
    game, players = data
    match = Match(1, game, "2026-10-01", 30, players[:2])
    with pytest.raises(ValueError):
        match.finish(players[2])


def test_find_and_filter(data):
    game, players = data
    other = Game(2, "Уно", 2, 6)
    matches = [
        Match(1, game, "2026-10-01", 30, players),
        Match(2, other, "2026-10-02", 20, players),
    ]
    assert find_match_by_id(matches, 2).game.title == "Уно"
    assert find_match_by_id(matches, 9) is None
    assert len(matches_for_game(matches, game)) == 1
