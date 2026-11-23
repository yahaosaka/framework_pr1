from datetime import date

from django.contrib import messages
from django.db import DatabaseError, IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from games.models import Game
from games.forms import GameForm
from homepage.parameters import bounded_int
from matches.models import Match


@require_http_methods(["GET", "POST"])
def game_edit(request, game_id=None):
    game = get_object_or_404(Game, pk=game_id) if game_id else None
    form = GameForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None, instance=game)
    if request.method == "POST" and form.is_valid():
        try:
            saved = form.save()
        except IntegrityError:
            form.add_error(None, "Название или слаг уже используются.")
        else:
            messages.success(request, "Игра сохранена.")
            return redirect("games:detail", game_id=saved.pk)
    return render(request, "games/game_form.html",
                  {"form": form, "game": game,
                   "heading": "Редактировать игру" if game else "Новая игра"})


def games(request):
    query = request.GET.get("q", "").strip()[:200]
    games_list = Game.objects.all()
    if query:
        games_list = games_list.filter(title__icontains=query)
    return render(request, "games/game_list.html",
                  {"games": games_list, "q": query})


def game_detail(request, game_id=None, slug=None):
    lookup = {"slug": slug} if slug is not None else {"pk": game_id}
    game = get_object_or_404(Game, **lookup)
    game_matches = game.matches.select_related("winner").order_by(
        "match_date", "pk")
    return render(request, "games/game_detail.html",
                  {"game": game, "matches": game_matches})


def available_games(request):
    value = request.GET.get("date", "").strip()
    selected_date, error = None, ""
    games = Game.objects.none()
    if value:
        try:
            selected_date = date.fromisoformat(value)
        except ValueError:
            error = "Введите корректную дату."
        else:
            occupied = Match.objects.blocking().for_date(
                selected_date).values_list("game_id", flat=True)
            try:
                games = list(Game.objects.exclude(pk__in=occupied))
            except DatabaseError:
                error = "Не удалось проверить доступность. Повторите позже."
                selected_date = None
    return render(request, "games/available.html", {
        "games": games, "selected_date": selected_date,
        "date_value": value, "error": error})


def game_search(request):
    value = request.GET.get("players", "").strip()
    query = request.GET.get("q", "").strip()[:200]
    count = bounded_int(value, 2, 6)
    error = ""
    results = Game.objects.none()
    if value and count is None:
        error = "Введите целое число игроков от 2 до 6."
    elif count is not None:
        results = Game.objects.filter(
            min_players__lte=count, max_players__gte=count)
        if query:
            results = results.filter(
                Q(title__icontains=query) | Q(genre__icontains=query))
    return render(request, "games/game_search.html", {
        "games": results, "player_count": count, "players_value": value,
        "q": query, "error": error})
