from models import Game, Match, Player
from storage import (
    load_games,
    load_matches,
    load_players,
    save_games,
    save_matches,
    save_players,
)


def test_games_and_players_roundtrip(tmp_path):
    games_file = str(tmp_path / "games.json")
    players_file = str(tmp_path / "players.json")
    save_games([Game(1, "Уно", 2, 6, "карточная")], games_file)
    save_players([Player(1, "Анна", "anna@example.com")], players_file)
    game = load_games(games_file)[0]
    player = load_players(players_file)[0]
    assert isinstance(game, Game) and game.title == "Уно"
    assert isinstance(player, Player) and player.email == "anna@example.com"


def test_load_matches_restores_links():
    games = load_games("data/games.json")
    players = load_players("data/players.json")
    matches = load_matches("data/matches.json", games, players)
    first = matches[0]
    assert isinstance(first, Match)
    assert first.game in games
    assert all(player in players for player in first.players)


def test_matches_roundtrip(tmp_path):
    games = load_games("data/games.json")
    players = load_players("data/players.json")
    matches = load_matches("data/matches.json", games, players)
    target = str(tmp_path / "matches.json")
    save_matches(matches, target)
    again = load_matches(target, games, players)
    assert [m.to_data() for m in again] == [m.to_data() for m in matches]


def test_missing_and_broken_file(tmp_path):
    assert load_games(str(tmp_path / "none.json")) == []
    broken = tmp_path / "broken.json"
    broken.write_text("{не json", encoding="utf-8")
    assert load_players(str(broken)) == []
