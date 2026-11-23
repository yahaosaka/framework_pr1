from datetime import timedelta
from io import BytesIO

import pytest
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client
from django.utils import timezone
from PIL import Image

from games.models import Game
from matches.forms import MatchFilterForm, MatchForm
from matches.models import Match
from matches.services import create_match
from players.models import Player

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    game = Game.objects.create(
        title="Тест форм", min_players=2, max_players=4)
    players = [Player.objects.create(name=n) for n in ("Игрок 1", "Игрок 2")]
    return game, players


def payload(catalog, days=1, **changes):
    game, players = catalog
    data = {
        "game": game.pk, "players": [p.pk for p in players],
        "match_date": str(timezone.localdate() + timedelta(days=days)),
        "duration_minutes": 60, "status": Match.Status.ACTIVE,
        "notes": "Тестовая заметка"}
    data.update(changes)
    return data


def test_filter_form_uses_typed_cleaned_data(client, catalog):
    game, players = catalog
    day = timezone.localdate() + timedelta(days=1)
    create_match(game, players, day, 60)
    form = MatchFilterForm({
        "game": game.pk, "player": players[0].pk, "date": str(day)})
    assert form.is_valid()
    assert form.cleaned_data["game"] == game
    assert form.cleaned_data["date"] == day
    assert not isinstance(form, forms.ModelForm)
    response = client.get("/matches/", form.data)
    assert response.context["filter_form"].is_valid()
    assert response.context["page_obj"].paginator.count == 1
    assert not client.get("/matches/").context["filter_form"].is_bound


@pytest.mark.parametrize("data", [
    {"date": "oops"}, {"game": "abc"}, {"game": 999999},
    {"player": "x"}, {"status": "not-a-status"},
    {"from": "2026-12-02", "to": "2026-12-01"},
])
def test_invalid_filter_is_visible(client, data):
    response = client.get("/matches/", data)
    assert response.status_code == 200
    assert response.context["filter_form"].errors
    assert response.context["errors"]


def test_model_form_get_initial_and_commit_false(client, catalog):
    form = MatchForm(payload(catalog))
    assert isinstance(form, forms.ModelForm)
    assert {"is_completed", "is_scheduled", "id"}.isdisjoint(form.fields)
    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    assert instance.pk is None
    assert not Match.objects.exists()
    response = client.get("/matches/new/")
    assert response.context["form"].initial["match_date"] == (
        timezone.localdate())
    html = response.content.decode()
    assert "form-control" in html and "<textarea" in html


@pytest.mark.parametrize("days", [0, 1])
def test_create_today_and_future_prg_and_notes(client, catalog, days):
    data = payload(catalog, days=days, is_completed=True)
    response = client.post("/matches/new/", data)
    assert response.status_code == 302
    match = Match.objects.get()
    assert match.players.count() == 2
    assert match.notes == "Тестовая заметка"
    assert not match.is_completed  # Подмена скрытого флага проигнорирована.
    assert client.get(response.url).status_code == 200
    assert client.get(response.url).status_code == 200
    assert Match.objects.count() == 1


@pytest.mark.parametrize("changes,field", [
    ({"match_date": "2000-01-01"}, "match_date"),
    ({"duration_minutes": 0}, "duration_minutes"),
    ({"duration_minutes": 1441}, "duration_minutes"),
    ({"match_date": ""}, "match_date"),
    ({"players": []}, "players"),
])
def test_invalid_create_preserves_values(client, catalog, changes, field):
    response = client.post("/matches/new/", payload(catalog, **changes))
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert not Match.objects.exists()
    assert "Тестовая заметка" in response.content.decode()


def test_busy_cancel_and_create_again(client, catalog):
    data = payload(catalog)
    assert client.post("/matches/new/", data).status_code == 302
    match = Match.objects.get()
    response = client.post("/matches/new/", data)
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert Match.objects.count() == 1
    cancel = f"/matches/{match.pk}/cancel/"
    assert client.get(cancel).status_code == 405
    assert client.post(cancel).status_code == 302
    match.refresh_from_db()
    assert match.status == Match.Status.CANCELLED
    assert client.post(cancel).status_code == 404
    assert client.post("/matches/new/", data).status_code == 302
    assert Match.objects.count() == 2
    assert Match.objects.cancelled().count() == 1


def test_edit_self_exclusion_and_other_conflict(client, catalog):
    game, players = catalog
    first = create_match(
        game, players, timezone.localdate() + timedelta(days=1), 60)
    second = create_match(
        game, players, timezone.localdate() + timedelta(days=2), 80)
    url = f"/matches/{first.pk}/edit/"
    response = client.get(url)
    assert response.context["form"].instance.pk == first.pk
    assert response.context["form"]["match_date"].value() == first.match_date
    assert client.post(url, payload(catalog)).status_code == 302
    assert Match.objects.count() == 2
    response = client.post(url, payload(
        catalog, match_date=second.match_date.isoformat()))
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    first.refresh_from_db()
    assert first.match_date != second.match_date
    response = client.post(url, payload(catalog, match_date="2000-01-01"))
    assert "match_date" in response.context["form"].errors


def test_historical_date_can_be_preserved(client, catalog):
    game, players = catalog
    old = timezone.localdate() - timedelta(days=30)
    match = create_match(game, players, old, 60)
    assert client.post(f"/matches/{match.pk}/edit/", payload(
        catalog, match_date=str(old), notes="История")).status_code == 302
    match.refresh_from_db()
    assert match.match_date == old and match.notes == "История"


def test_unique_constraint_prevents_racing_writes(catalog):
    game, players = catalog
    day = timezone.localdate()
    create_match(game, players, day, 60)
    with pytest.raises(IntegrityError), transaction.atomic():
        Match.objects.create(
            game=game, match_date=day, duration_minutes=60,
            status=Match.Status.SCHEDULED, is_scheduled=True)
    assert Match.objects.count() == 1


def test_delete_confirmation_and_csrf(client, catalog):
    game, players = catalog
    match = create_match(game, players, timezone.localdate(), 60)
    url = f"/matches/{match.pk}/delete/"
    assert client.get(url).status_code == 200
    assert Match.objects.filter(pk=match.pk).exists()
    secure = Client(enforce_csrf_checks=True)
    assert secure.post(url).status_code == 403
    assert secure.post(f"/matches/{match.pk}/cancel/").status_code == 403
    assert secure.post("/matches/new/", payload(catalog)).status_code == 403
    assert secure.post(f"/matches/{match.pk}/edit/", payload(
        catalog)).status_code == 403
    assert client.post(url).status_code == 302
    assert not Match.objects.exists()
    assert Player.objects.count() == 2 and Game.objects.count() == 1


@pytest.mark.parametrize("url", [
    "/matches/999999/edit/", "/matches/999999/delete/"])
def test_missing_forms_return_404(client, url):
    assert client.get(url).status_code == 404


def png_upload(name="game.png", color="blue"):
    output = BytesIO()
    Image.new("RGB", (32, 32), color).save(output, format="PNG")
    return SimpleUploadedFile(
        name, output.getvalue(), content_type="image/png")


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


def game_payload(**changes):
    data = {
        "title": "Игра с фото", "min_players": 2, "max_players": 4,
        "genre": "учебная"}
    data.update(changes)
    return data


def test_image_upload_replace_clear_and_preview(client, media):
    response = client.post("/games/new/", game_payload(image=png_upload()))
    assert response.status_code == 302
    game = Game.objects.get()
    assert game.image.storage.exists(game.image.name)
    assert str(game.image.path).startswith(str(media))
    page = client.get(response.url).content.decode()
    assert game.image.url in page and "<img" in page
    old = game.image.name
    response = client.post(f"/games/{game.pk}/edit/", game_payload(
        image=png_upload("second.png", "red")))
    assert response.status_code == 302
    game.refresh_from_db()
    assert game.image.name != old
    assert client.post(f"/games/{game.pk}/edit/", game_payload(
        **{"image-clear": "on"})).status_code == 302
    game.refresh_from_db()
    assert not game.image
    assert "Изображение не загружено" in client.get(
        game.get_absolute_url()).content.decode()


def test_invalid_image_and_size_do_not_save(client, media):
    fake = SimpleUploadedFile(
        "fake.jpg", b"not an image", content_type="image/jpeg")
    response = client.post("/games/new/", game_payload(image=fake))
    assert response.status_code == 200
    assert response.context["form"].errors["image"]
    assert not Game.objects.exists()
    large = png_upload()
    content = large.read() + b"\0" * (5 * 1024 * 1024)
    response = client.post("/games/new/", game_payload(
        image=SimpleUploadedFile("large.png", content, "image/png")))
    assert response.context["form"].errors["image"]
    assert not Game.objects.exists()


def test_admin_image_upload(client, admin_user, media):
    game = Game.objects.create(
        title="Фото Admin", min_players=2, max_players=4)
    client.force_login(admin_user)
    data = game_payload(
        title=game.title, slug=game.slug, image=png_upload("admin.png"))
    data.update({
        "matches-TOTAL_FORMS": 0, "matches-INITIAL_FORMS": 0,
        "matches-MIN_NUM_FORMS": 0, "matches-MAX_NUM_FORMS": 0,
        "_save": "Сохранить"})
    assert client.post(
        f"/admin/games/game/{game.pk}/change/", data).status_code == 302
    game.refresh_from_db()
    assert game.image.storage.exists(game.image.name)


def test_admin_action_conflict_is_message_not_500(client, admin_user, catalog):
    game, players = catalog
    first = create_match(game, players, timezone.localdate(), 60)
    first.cancel()
    create_match(game, players, timezone.localdate(), 60)
    client.force_login(admin_user)
    response = client.post("/admin/matches/match/", {
        "action": "mark_active", "_selected_action": [first.pk], "index": 0},
        follow=True)
    assert response.status_code == 200
    first.refresh_from_db()
    assert first.status == Match.Status.CANCELLED
