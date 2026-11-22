from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from db.orm_import import import_source
from games.models import Game
from matches.models import Match, MatchPlayer
from matches.services import create_match, finish_match
from players.models import Player

pytestmark = pytest.mark.django_db


@pytest.fixture
def imported():
    from django.conf import settings
    source = settings.BASE_DIR / "data" / "boardgames.sqlite"
    counts = import_source(source)
    return source, counts


def test_import_preserves_all_fields_and_links(imported):
    import sqlite3
    from contextlib import closing

    source, counts = imported
    assert counts == (6, 5, 8, 23)
    before = source.read_bytes()
    assert import_source(source) == counts
    assert source.read_bytes() == before
    assert Game.objects.count() == 6
    assert Player.objects.count() == 5
    assert Match.objects.count() == 8
    with closing(sqlite3.connect(source)) as conn:
        for row in conn.execute("SELECT * FROM matches"):
            obj = Match.objects.get(pk=row[0])
            assert (obj.game_id, obj.match_date.isoformat(),
                    obj.duration_minutes, obj.winner_id,
                    obj.is_completed) == tuple(row[1:])
        old_links = set(conn.execute(
            "SELECT match_id, player_id FROM match_players"))
    assert set(MatchPlayer.objects.values_list(
        "match_id", "player_id")) == old_links


def test_bad_import_rolls_back(imported, tmp_path):
    import sqlite3

    source, _ = imported
    broken = tmp_path / "bad.sqlite"
    broken.write_bytes(source.read_bytes())
    with sqlite3.connect(broken) as conn:
        conn.execute("UPDATE games SET title='Changed' WHERE id=1")
        conn.execute(
            "UPDATE matches SET winner_id=5 WHERE id=1")
    original = Game.objects.get(pk=1).title
    with pytest.raises(ValidationError):
        import_source(broken)
    assert Game.objects.get(pk=1).title == original


def test_crud_and_domain_rules(imported):
    game = Game.objects.get(pk=1)
    one, two = list(Player.objects.order_by("pk")[:2])
    match = create_match(game, [one, two], date(2026, 11, 16), 60)
    assert match.players.count() == 2
    with pytest.raises(ValidationError):
        finish_match(match.pk, Player.objects.get(pk=5))
    result = finish_match(match.pk, one)
    assert result.is_completed and result.winner_id == one.pk
    with pytest.raises(ValidationError):
        finish_match(match.pk, two)
    with pytest.raises(ProtectedError):
        game.delete()
    match.delete()
    assert not MatchPlayer.objects.filter(match_id=match.pk).exists()
    with pytest.raises(ValidationError):
        create_match(game, [one, one], date.today(), 30)
    with pytest.raises(ValidationError):
        create_match(game, [one, two], date.today(), 0)


def test_db_constraints(imported):
    with pytest.raises(IntegrityError), transaction.atomic():
        Game.objects.create(title="Invalid", min_players=6, max_players=2)
    match = Match.objects.first()
    link = match.participations.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        MatchPlayer.objects.create(match=match, player=link.player)


@pytest.mark.parametrize("url", [
    "/", "/games/", "/games/1/", "/games/search/?players=4",
    "/matches/", "/matches/1/", "/matches/statistics/",
])
def test_existing_pages(client, imported, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url", [
    "/games/9999/", "/matches/9999/", "/missing/",
])
def test_not_found(client, url):
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("value", ["0", "7", "abc", "²", "9" * 5000])
def test_invalid_player_count(client, imported, value):
    response = client.get("/games/search/", {"players": value})
    assert response.status_code == 200
    assert response.context["error"]


def test_searches_and_combined_filters(client, imported):
    response = client.get("/games/", {"q": "Уно"})
    assert [g.title for g in response.context["games"]] == ["Уно"]
    response = client.get("/games/search/", {"players": 4, "q": "стратег"})
    assert {g.pk for g in response.context["games"]} == {1, 2}
    response = client.get("/matches/", {
        "game": 1, "status": "completed", "from": "2026-09-10",
        "to": "2026-10-31", "sort": "-date",
    })
    assert [m.pk for m in response.context["matches"]] == [7, 4]
    response = client.get("/matches/", {"status": "active"})
    assert [m.pk for m in response.context["matches"]] == [8]
    response = client.get("/matches/", {"q": "карточная"})
    assert [m.pk for m in response.context["matches"]] == [2]


@pytest.mark.parametrize("params", [
    {"game": "x"}, {"from": "not-date"}, {"sort": "DROP TABLE"},
    {"from": "2026-11-10", "to": "2026-01-01"},
    {"status": "invalid"}, {"game": "9" * 5000},
])
def test_bad_filter_parameters(client, imported, params):
    response = client.get("/matches/", params)
    assert response.status_code == 200
    assert response.context["errors"]


def test_pagination_preserves_query(client, imported):
    response = client.get("/matches/", {"sort": "-date"})
    assert len(response.context["matches"]) == 5
    assert "sort=-date&amp;page=2" in response.content.decode()
    response = client.get("/matches/", {"sort": "-date", "page": 2})
    assert len(response.context["matches"]) == 3
    for page in ["abc", "-1", "999999"]:
        assert client.get("/matches/", {"page": page}).status_code == 200


def test_statistics_no_join_multiplication(client, imported):
    response = client.get("/matches/statistics/")
    context = response.context
    assert context["totals"]["matches_count"] == 8
    assert context["totals"]["completed_count"] == 7
    assert context["totals"]["total_minutes"] == 760
    assert sum(p.wins for p in context["rating"]) == 7
    assert sum(p.played for p in context["rating"]) == 23
    assert [g.pk for g in context["unplayed"]] == [6]


def test_empty_database(client):
    for url in ["/games/", "/matches/", "/matches/statistics/"]:
        assert client.get(url).status_code == 200
    stats = client.get("/matches/statistics/").context["totals"]
    assert stats["matches_count"] == 0


def test_detail_query_count_is_constant(client, imported,
                                        django_assert_num_queries):
    with django_assert_num_queries(2):
        assert client.get("/matches/1/").status_code == 200


def test_crud_demo_leaves_no_changes(imported):
    before = (Game.objects.count(), Player.objects.count(),
              Match.objects.count())
    call_command("orm_demo")
    assert (Game.objects.count(), Player.objects.count(),
            Match.objects.count()) == before
