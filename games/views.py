from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from games.models import Game
from games.forms import GameForm
from homepage.parameters import bounded_int


@require_http_methods(["GET", "POST"])
def game_edit(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    form = GameForm(
        request.POST if request.method == "POST" else None, instance=game)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("games:detail", game_id=game.pk)
    return render(request, "games/game_form.html",
                  {"form": form, "game": game})


def games(request):
    query = request.GET.get("q", "").strip()[:200]
    games_list = Game.objects.all()
    if query:
        games_list = games_list.filter(title__icontains=query)
    return render(request, "games/game_list.html",
                  {"games": games_list, "q": query})


def game_detail(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    game_matches = game.matches.select_related("winner").order_by(
        "match_date", "pk")
    return render(request, "games/game_detail.html",
                  {"game": game, "matches": game_matches})


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
