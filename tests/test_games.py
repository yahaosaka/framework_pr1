import pytest

from models.games import (
    Game,
    add_game,
    check_game_players,
    filter_games_by_players,
    find_game,
    find_game_by_id,
    sort_games,
)


@pytest.fixture
def games():
    return [
        Game(1, "Каркассон", 2, 5, "стратегия"),
        Game(2, "Колонизаторы", 3, 4, "стратегия"),
        Game(3, "Уно", 2, 6, "карточная"),
    ]


def test_game_creation(games):
    game = games[0]
    assert game.id == 1 and game.title == "Каркассон"
    assert (game.min_players, game.max_players) == (2, 5)
    assert "Каркассон" in str(game)


def test_validate_players():
    assert Game.validate_players(2, 4)
    assert not Game.validate_players(5, 3)
    assert not Game.validate_players(1, 4)


def test_is_suitable_for(games):
    assert games[1].is_suitable_for(3)
    assert not games[1].is_suitable_for(2)


def test_add_game(games):
    game = add_game(games, "Шакал", 2, 4, "приключения")
    assert game.id == 4
    assert games[-1] is game


def test_add_game_validation(games):
    with pytest.raises(ValueError):
        add_game(games, "", 2, 4)
    with pytest.raises(ValueError):
        add_game(games, "Плохая", 5, 3)


def test_find(games):
    assert find_game(games, "кол")[0].id == 2
    assert find_game_by_id(games, 3).title == "Уно"
    assert find_game_by_id(games, 99) is None


def test_filter_and_sort(games):
    assert [g.id for g in filter_games_by_players(games, 6)] == [3]
    assert sort_games(games)[0].title == "Каркассон"
    assert sort_games(games, by="players")[0].title == "Уно"


def test_roundtrip(games):
    assert Game.from_data(games[0].to_data()).title == "Каркассон"


def test_check_game_players(games):
    assert check_game_players(games, 2, 3)
    assert not check_game_players(games, 2, 6)
    assert not check_game_players(games, 99, 3)
