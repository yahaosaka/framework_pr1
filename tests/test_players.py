import pytest

from models.players import Player, add_player, find_player, find_player_by_id


@pytest.fixture
def players():
    return [Player(1, "Анна", "anna@example.com"), Player(2, "Борис")]


def test_player_creation(players):
    player = players[0]
    assert (player.id, player.name) == (1, "Анна")
    assert player.email == "anna@example.com"
    assert str(player) == "[1] Анна"


def test_add_player(players):
    player = add_player(players, "Вика", "vika@example.com")
    assert player.id == 3


def test_add_player_empty(players):
    with pytest.raises(ValueError):
        add_player(players, "   ")


def test_find_player(players):
    assert find_player(players, "anna")[0].name == "Анна"
    assert find_player_by_id(players, 2).name == "Борис"
    assert find_player_by_id(players, 5) is None


def test_from_data():
    assert str(Player.from_data({"id": 7, "name": "Глеб"})) == "[7] Глеб"
