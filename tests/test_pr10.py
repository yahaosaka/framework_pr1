from datetime import date
from unittest.mock import patch

import pytest
from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.core.management import call_command

from games.models import Game
from matches.models import Match
from matches.services import change_status, create_match
from players.models import Player

pytestmark = pytest.mark.django_db


def test_demo_command_is_repeatable_without_resetting_status():
    call_command("pr10_demo")
    match = Match.objects.get()
    change_status(match.pk, Match.Status.CANCELLED, None)
    call_command("pr10_demo")
    match.refresh_from_db()
    assert Match.objects.count() == 1
    assert match.status == Match.Status.CANCELLED


@pytest.fixture
def party():
    game = Game.objects.create(
        title="Каркассон", min_players=2, max_players=6, genre="стратегия")
    players = [Player.objects.create(name=name) for name in ("Анна", "Иван")]
    return create_match(game, players, date(2026, 11, 22), 60)


def test_slug_generated_field_and_old_urls(client, party):
    game = party.game
    assert game.slug == "karkasson"
    assert client.get(game.get_absolute_url()).status_code == 200
    assert client.get(f"/games/{game.pk}/").status_code == 200
    assert client.get("/games/by-slug/missing-game/").status_code == 404
    game.refresh_from_db()
    assert game.is_large_group
    game.max_players = 4
    game.save()
    game.refresh_from_db()
    assert not game.is_large_group
    game.title = "Новое название"
    game.save()
    assert game.slug == "karkasson"
    collision = Game.objects.create(
        title="Karkasson", min_players=2, max_players=4)
    assert collision.slug == "karkasson-2"


def test_manager_and_availability(client, party):
    day = party.match_date
    assert Match.objects.active().for_date(day).get() == party
    response = client.get("/games/available/", {"date": str(day)})
    assert party.game not in response.context["games"]
    change_status(party.pk, Match.Status.SCHEDULED, None)
    assert Match.objects.scheduled().count() == 1
    assert Match.objects.blocking().for_date(day).count() == 1
    change_status(party.pk, Match.Status.CANCELLED, None)
    assert Match.objects.cancelled().for_date(day).count() == 1
    response = client.get("/games/available/", {"date": str(day)})
    assert party.game in response.context["games"]
    assert client.get("/matches/statistics/").context[
        "totals"]["cancelled_count"] == 1
    assert sum(p.played for p in client.get(
        "/matches/statistics/").context["rating"]) == 0
    assert client.get("/games/available/", {"date": "invalid"}).context[
        "error"]


def test_availability_database_error_is_readable(client, party):
    # Ошибка имитируется только в проверке доступности.
    with patch("games.views.Game.objects.exclude",
               side_effect=DatabaseError("test failure")):
        response = client.get(
            "/games/available/", {"date": str(party.match_date)})
    assert response.status_code == 200
    assert "Повторите позже" in response.context["error"]
    assert "test failure" not in response.content.decode()


def test_context_and_values_list_filters(client, party):
    for url in ("/", "/games/", f"/matches/{party.pk}/"):
        response = client.get(url)
        assert response.context["games_count"] == 1
        assert "Игр в каталоге: 1" in response.content.decode()
    player = party.players.first()
    page = client.get("/matches/", {
        "player": player.pk, "date": str(party.match_date)})
    row = list(page.context["matches"])[0]
    assert row["game_title"] == party.game.title
    assert row["player_count"] == 2
    assert client.get("/matches/", {"player": "bad"}).context["errors"]
    assert client.get("/matches/", {"date": "bad"}).context["errors"]


def status_payload(party, status, winner=""):
    links = list(party.participations.order_by("pk"))
    data = {
        "game": party.game_id, "match_date": str(party.match_date),
        "duration_minutes": 60, "status": status, "winner": winner,
        "participations-TOTAL_FORMS": len(links),
        "participations-INITIAL_FORMS": len(links),
        "participations-MIN_NUM_FORMS": 0,
        "participations-MAX_NUM_FORMS": 1000,
        "_save": "Сохранить",
    }
    for index, link in enumerate(links):
        data.update({
            f"participations-{index}-id": link.pk,
            f"participations-{index}-match": party.pk,
            f"participations-{index}-player": link.player_id})
    return data


def test_admin_lists_access_and_status_form(client, admin_user, party):
    assert client.get("/admin/").status_code == 302
    client.force_login(admin_user)
    for url in (
            "/admin/", "/admin/games/game/", "/admin/players/player/",
            "/admin/matches/match/",
            f"/admin/games/game/{party.game_id}/change/",
            f"/admin/matches/match/{party.pk}/change/"):
        response = client.get(url)
        assert response.status_code == 200
    url = f"/admin/matches/match/{party.pk}/change/"
    winner = party.players.first()
    response = client.post(url, status_payload(
        party, Match.Status.COMPLETED, winner.pk))
    assert response.status_code == 302
    party.refresh_from_db()
    assert party.status == Match.Status.COMPLETED
    assert party.winner == winner
    response = client.post(url, status_payload(
        party, Match.Status.CANCELLED, winner.pk))
    assert response.status_code == 302
    party.refresh_from_db()
    assert party.status == Match.Status.CANCELLED
    assert party.winner is None


def test_admin_rejects_foreign_winner_and_invalid_roster(
        client, admin_user, party):
    client.force_login(admin_user)
    outsider = Player.objects.create(name="Не участник")
    url = f"/admin/matches/match/{party.pk}/change/"
    response = client.post(url, status_payload(
        party, Match.Status.COMPLETED, outsider.pk))
    assert response.status_code == 200
    party.refresh_from_db()
    assert party.status == Match.Status.ACTIVE
    data = status_payload(party, Match.Status.ACTIVE)
    data["participations-0-DELETE"] = "on"
    response = client.post(url, data)
    assert response.status_code == 200
    assert party.players.count() == 2


def test_admin_game_inline_edit_and_bulk_cancel(client, admin_user, party):
    client.force_login(admin_user)
    game = party.game
    data = {
        "title": game.title, "slug": game.slug, "genre": game.genre,
        "min_players": game.min_players, "max_players": game.max_players,
        "matches-TOTAL_FORMS": 1, "matches-INITIAL_FORMS": 1,
        "matches-MIN_NUM_FORMS": 0, "matches-MAX_NUM_FORMS": 0,
        "matches-0-id": party.pk, "matches-0-game": game.pk,
        "matches-0-match_date": str(party.match_date),
        "matches-0-duration_minutes": 75, "_save": "Сохранить"}
    response = client.post(
        f"/admin/games/game/{game.pk}/change/", data)
    assert response.status_code == 302
    party.refresh_from_db()
    assert party.duration_minutes == 75
    response = client.post("/admin/matches/match/", {
        "action": "mark_cancelled", "_selected_action": [party.pk],
        "index": 0})
    assert response.status_code == 302
    party.refresh_from_db()
    assert party.status == Match.Status.CANCELLED
    response = client.get("/admin/matches/match/", {
        "q": "Каркассон", "status__exact": "cancelled"})
    assert response.status_code == 200
    assert response.context["cl"].result_count == 1


@pytest.mark.django_db(transaction=True)
def test_status_data_migration_preserves_completed_and_scheduled():
    before = [
        ("games", "0002_pr10_games"),
        ("players", "0002_alter_player_options"),
        ("matches", "0002_match_is_scheduled_and_more")]
    executor = MigrationExecutor(connection)
    after = executor.loader.graph.leaf_nodes()
    executor.migrate(before)
    old = executor.loader.project_state(before).apps
    GameOld = old.get_model("games", "Game")
    PlayerOld = old.get_model("players", "Player")
    MatchOld = old.get_model("matches", "Match")
    game = GameOld.objects.create(
        title="Миграция", slug="migration-test",
        min_players=2, max_players=4)
    player = PlayerOld.objects.create(name="Участник")
    common = dict(game_id=game.pk, match_date="2026-11-22",
                  duration_minutes=40)
    completed = MatchOld.objects.create(
        **common, is_completed=True, winner_id=player.pk)
    scheduled = MatchOld.objects.create(**common, is_scheduled=True)
    active = MatchOld.objects.create(
        game_id=game.pk, match_date="2026-11-23", duration_minutes=40)
    try:
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        new = executor.loader.project_state(after).apps.get_model(
            "matches", "Match")
        assert new.objects.get(pk=completed.pk).status == "completed"
        assert new.objects.get(pk=completed.pk).winner_id == player.pk
        assert new.objects.get(pk=scheduled.pk).status == "scheduled"
        assert new.objects.get(pk=active.pk).status == "active"
    finally:
        MigrationExecutor(connection).migrate(after)
