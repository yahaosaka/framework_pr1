from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from games.models import Game
from matches.services import change_status, create_match, finish_match
from players.models import Player

pytestmark = pytest.mark.django_db


def test_three_statuses_preserve_match_data(client):
    game = Game.objects.create(title="Тест", min_players=2, max_players=6)
    players = [Player.objects.create(name=n) for n in ("А", "Б")]
    match = create_match(game, players, date(2026, 11, 17), 40)
    url = f"/matches/{match.pk}/"
    for status, label in (
            ("completed", "Завершена"), ("scheduled", "Будет идти"),
            ("active", "Идет"), ("scheduled", "Будет идти"),
            ("completed", "Завершена")):
        response = client.post(url, {
            "status": status, "winner": players[0].pk})
        assert response.status_code == 302
        match.refresh_from_db()
        assert match.status == status
        assert match.get_status_display() == label
        assert match.is_completed == (status == "completed")
        assert match.winner_id == (
            players[0].pk if status == "completed" else None)
        assert match.game_id == game.pk
        assert match.match_date == date(2026, 11, 17)
        assert match.duration_minutes == 40
        assert set(match.players.all()) == set(players)
        assert label in client.get(url).content.decode()
        assert label in client.get(f"/games/{game.pk}/").content.decode()
        page = client.get("/matches/", {"status": status})
        assert [obj["id"] for obj in page.context["matches"]] == [match.pk]
        for other in {"active", "scheduled", "completed"} - {status}:
            assert not client.get(
                "/matches/", {"status": other}).context["matches"]
    with pytest.raises(ValidationError):
        change_status(match.pk, "invalid", players[0])


def test_scheduled_has_no_wins_and_can_start_without_winner(client):
    game = Game.objects.create(title="Тест", min_players=2, max_players=4)
    players = [Player.objects.create(name=n) for n in ("А", "Б")]
    match = create_match(game, players, date(2026, 11, 17), 40)
    change_status(match.pk, "scheduled", None)
    assert client.post(
        f"/matches/{match.pk}/", {"status": "active"}).status_code == 302
    match.refresh_from_db()
    assert match.status == "active"
    assert match.winner_id is None
    change_status(match.pk, "scheduled", None)
    rating = client.get("/matches/statistics/").context["rating"]
    assert sum(obj.wins for obj in rating) == 0
    assert sum(obj.played for obj in rating) == 0
    # Старый shell-сервис тоже сохраняет согласованный статус.
    finish_match(match.pk, players[0])
    match.refresh_from_db()
    assert match.status == "completed" and not match.is_scheduled


def test_create_and_edit_scheduled(client):
    game = Game.objects.create(title="Тест", min_players=2, max_players=4)
    players = [Player.objects.create(name=n) for n in ("А", "Б")]
    data = {
        "game": game.pk, "players": [p.pk for p in players],
        "match_date": timezone.localdate().isoformat(), "duration_minutes": 40,
        "status": "scheduled"}
    assert client.post("/matches/new/", data).status_code == 302
    match = game.matches.get()
    assert match.status == "scheduled"
    assert client.get(f"/matches/{match.pk}/edit/").context[
        "form"].initial["status"] == "scheduled"
    assert client.post(
        f"/matches/{match.pk}/edit/", data).status_code == 302
    match.refresh_from_db()
    assert match.status == "scheduled"
