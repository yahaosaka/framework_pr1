from datetime import date, timedelta
from django.utils import timezone

import pytest
from django.test import Client

from games.models import Game
from matches.models import Match
from matches.services import create_match
from players.models import Player

pytestmark = pytest.mark.django_db


@pytest.fixture
def party():
    game = Game.objects.create(
        title="Уно", min_players=2, max_players=6, genre="карточная")
    players = [Player.objects.create(name=name) for name in ("Анна", "Иван")]
    return create_match(game, players, date(2026, 11, 17), 30)


def test_finish_reopen_and_rating(client, party):
    url = f"/matches/{party.pk}/"
    winner = party.players.first()
    assert client.get(url).status_code == 200
    response = client.post(url, {
        "status": "completed", "winner": winner.pk})
    assert response.status_code == 302
    party.refresh_from_db()
    assert party.is_completed and party.winner_id == winner.pk
    stats = client.get("/matches/statistics/").context
    assert stats["totals"]["completed_count"] == 1
    assert sum(player.wins for player in stats["rating"]) == 1
    assert client.post(url, {"status": "active"}).status_code == 302
    party.refresh_from_db()
    assert not party.is_completed and party.winner_id is None
    stats = client.get("/matches/statistics/").context
    assert stats["totals"]["completed_count"] == 0
    assert sum(player.wins for player in stats["rating"]) == 0


def test_status_rejects_missing_or_foreign_winner(client, party):
    outsider = Player.objects.create(name="Посторонний")
    for data in (
            {"status": "completed"},
            {"status": "completed", "winner": outsider.pk},
            {"status": "invalid"}):
        response = client.post(f"/matches/{party.pk}/", data)
        assert response.status_code == 200
        assert response.context["status_form"].errors
        party.refresh_from_db()
        assert not party.is_completed and party.winner_id is None


def test_edit_completed_party_and_roster_atomically(client, party):
    edited_date = timezone.localdate() + timedelta(days=1)
    third = Player.objects.create(name="Новый участник")
    first = party.players.first()
    response = client.post(f"/matches/{party.pk}/edit/", {
        "game": party.game_id, "players": [first.pk, third.pk],
        "match_date": edited_date.isoformat(), "duration_minutes": 80,
        "status": "completed", "winner": third.pk})
    assert response.status_code == 302
    party.refresh_from_db()
    assert party.winner_id == third.pk
    assert party.duration_minutes == 80
    assert party.match_date == edited_date
    assert set(party.players.values_list(
        "pk", flat=True)) == {first.pk, third.pk}
    # Удалить победителя из состава без смены результата нельзя.
    response = client.post(f"/matches/{party.pk}/edit/", {
        "game": party.game_id, "players": [first.pk],
        "match_date": "2026-11-19", "duration_minutes": 0,
        "status": "completed", "winner": third.pk})
    assert response.status_code == 200
    assert response.context["form"].errors
    party.refresh_from_db()
    assert party.duration_minutes == 80
    assert party.players.count() == 2


def test_create_on_site(client, party):
    assert client.get("/matches/new/").status_code == 200
    data = {
        "game": party.game_id,
        "players": list(party.players.values_list("pk", flat=True)),
        "match_date": (timezone.localdate() + timedelta(days=2)).isoformat(),
        "duration_minutes": 50,
        "status": "active"}
    response = client.post("/matches/new/", data)
    assert response.status_code == 302
    created = Match.objects.exclude(pk=party.pk).get()
    assert created.players.count() == 2
    assert not created.is_completed
    assert client.get(response.url).status_code == 200


def test_game_rename_and_validation(client, party):
    url = f"/games/{party.game_id}/edit/"
    assert client.get(url).status_code == 200
    assert client.post(url, {
        "title": "Дурак", "min_players": 2, "max_players": 6,
        "genre": "карточная"}).status_code == 302
    party.refresh_from_db()
    assert party.game.title == "Дурак"
    response = client.post(url, {
        "title": "Ошибка", "min_players": 6, "max_players": 2})
    assert response.context["form"].errors
    party.game.refresh_from_db()
    assert party.game.title == "Дурак"
    Game.objects.create(title="Занято", min_players=2, max_players=4)
    response = client.post(url, {
        "title": "Занято", "min_players": 2, "max_players": 6})
    assert response.context["form"].errors


def test_post_requires_csrf_and_get_never_changes_status(party):
    client = Client(enforce_csrf_checks=True)
    url = f"/matches/{party.pk}/"
    assert client.post(url, {"status": "active"}).status_code == 403
    assert client.get(url, {"status": "completed"}).status_code == 200
    party.refresh_from_db()
    assert not party.is_completed
    response = client.get(url)
    token = response.cookies["csrftoken"].value
    response = client.post(url, {
        "status": "completed", "winner": party.players.first().pk,
        "csrfmiddlewaretoken": token})
    assert response.status_code == 302


@pytest.mark.parametrize("url", [
    "/matches/999999/edit/", "/games/999999/edit/"])
def test_unknown_edit_target(client, url):
    assert client.get(url).status_code == 404
