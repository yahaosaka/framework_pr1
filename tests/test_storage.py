from storage import load_games, load_matches, save_games, save_matches


def test_games_roundtrip(tmp_path):
    path = str(tmp_path / "games.json")
    games = {1: {"id": 1, "title": "Шахматы", "min_players": 2,
                 "max_players": 2, "genre": "классика"}}
    save_games(games, path)
    assert load_games(path) == games


def test_matches_roundtrip(tmp_path):
    path = str(tmp_path / "matches.json")
    matches = [{"id": 1, "game_id": 1, "match_date": "2026-09-15",
                "player_count": 2, "duration_minutes": 30,
                "winner": "", "is_completed": False}]
    save_matches(matches, path)
    assert load_matches(path) == matches


def test_missing_and_broken_file(tmp_path):
    assert load_games(str(tmp_path / "none.json")) == {}
    broken = tmp_path / "broken.json"
    broken.write_text("{не json", encoding="utf-8")
    assert load_matches(str(broken)) == []
