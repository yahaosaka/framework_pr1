from datetime import date

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from games.models import Game
from homepage.parameters import bounded_int
from matches.models import Match
from matches.forms import MatchForm, StatusForm
from matches.services import change_status, save_match
from models.matches import check_duration
from players.models import Player

SORTS = {
    "date": ("match_date", "pk"),
    "-date": ("-match_date", "-pk"),
    "game": ("game__title", "match_date", "pk"),
    "duration": ("duration_minutes", "pk"),
}


def matches(request):
    rows = Match.objects.select_related("game", "winner").annotate(
        player_count=Count("players"))
    errors = []
    q = request.GET.get("q", "").strip()[:200]
    if q:
        rows = rows.filter(
            Q(game__title__icontains=q) | Q(game__genre__icontains=q))
    game_value = request.GET.get("game", "")
    if game_value:
        game_id = bounded_int(game_value, 1, 2147483647)
        if game_id is None:
            errors.append("Некорректный идентификатор игры.")
            rows = rows.none()
        else:
            rows = rows.filter(game_id=game_id)
    status = request.GET.get("status", "")
    if status == "completed":
        rows = rows.filter(is_completed=True)
    elif status == "scheduled":
        rows = rows.filter(is_scheduled=True)
    elif status == "active":
        rows = rows.exclude(is_completed=True).filter(is_scheduled=False)
    elif status:
        errors.append("Неизвестный статус.")
    dates = {}
    for key, lookup in (
            ("from", "match_date__gte"), ("to", "match_date__lte")):
        value = request.GET.get(key, "")
        if value:
            try:
                dates[key] = date.fromisoformat(value)
                rows = rows.filter(**{lookup: dates[key]})
            except ValueError:
                errors.append("Некорректная дата.")
                rows = rows.none()
    if "from" in dates and "to" in dates and dates["from"] > dates["to"]:
        errors.append("Начало периода позже окончания.")
        rows = rows.none()
    sort = request.GET.get("sort", "date")
    if sort not in SORTS:
        errors.append("Неизвестная сортировка; используется дата.")
        sort = "date"
    rows = rows.order_by(*SORTS[sort])
    page = Paginator(rows, 5).get_page(request.GET.get("page"))
    return render(request, "matches/match_list.html", {
        "matches": page.object_list, "page_obj": page,
        "games": Game.objects.all(), "errors": errors, "sort": sort,
    })


@require_http_methods(["GET", "POST"])
def match_detail(request, match_id):
    match = get_object_or_404(
        Match.objects.select_related("game", "winner").prefetch_related(
            "players"), pk=match_id)
    form = StatusForm(
        request.POST if request.method == "POST" else None, match=match)
    if request.method == "POST" and form.is_valid():
        try:
            change_status(
                match.pk, form.cleaned_data["status"],
                form.cleaned_data["winner"])
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("matches:detail", match_id=match.pk)
    return render(request, "matches/match_detail.html", {
        "match": match, "players": match.players.all(),
        "status_form": form,
        "duration_check": check_duration(match.duration_minutes)})


@require_http_methods(["GET", "POST"])
def match_edit(request, match_id=None):
    match = get_object_or_404(Match, pk=match_id) if match_id else None
    initial = {}
    if match:
        initial = {
            "game": match.game_id, "players": match.players.all(),
            "match_date": match.match_date.isoformat(),
            "duration_minutes": match.duration_minutes,
            "status": match.status,
            "winner": match.winner_id}
    form = MatchForm(
        request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        try:
            saved = save_match(match_id=match_id, **data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("matches:detail", match_id=saved.pk)
    return render(request, "matches/match_form.html", {
        "form": form,
        "heading": "Редактировать партию" if match else "Новая партия"})


def statistics(request):
    totals = Match.objects.aggregate(
        matches_count=Count("pk"),
        completed_count=Count("pk", filter=Q(is_completed=True)),
        avg_minutes=Avg("duration_minutes"),
        min_minutes=Min("duration_minutes"),
        max_minutes=Max("duration_minutes"),
        total_minutes=Sum("duration_minutes"))
    by_game = Game.objects.values(
        game_id=F("pk"), game_title=F("title")).annotate(
        matches_count=Count("matches"),
        avg_minutes=Avg("matches__duration_minutes")).order_by(
        "-matches_count", "game_title")
    rating = Player.objects.annotate(
        played=Count("matches", distinct=True,
                     filter=Q(matches__is_scheduled=False)),
        wins=Count("won_matches", distinct=True)).order_by(
        "-wins", "-played", "name", "pk")
    minimum = bounded_int(request.GET.get("min", "1"), 0, 2147483647)
    minimum = 1 if minimum is None else minimum
    popular = Game.objects.values(game_title=F("title")).annotate(
        matches_count=Count("matches")).filter(
        matches_count__gt=minimum).order_by("-matches_count", "game_title")
    genres = Game.objects.values("genre").annotate(
        games_count=Count("pk")).order_by("-games_count", "genre")
    unplayed = Game.objects.exclude(matches__isnull=False)
    return render(request, "matches/statistics.html", {
        "totals": totals, "by_game": by_game, "rating": rating,
        "popular": popular, "min_matches": minimum,
        "by_genre": genres, "unplayed": unplayed})
