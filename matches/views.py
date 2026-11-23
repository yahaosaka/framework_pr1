from django.contrib import messages
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from games.models import Game
from homepage.parameters import bounded_int
from matches.models import Match
from matches.forms import MatchFilterForm, MatchForm, StatusForm
from matches.services import change_status, validate_availability
from models.matches import check_duration
from players.models import Player

SORTS = {
    "date": ("match_date", "pk"),
    "-date": ("-match_date", "-pk"),
    "game": ("game__title", "match_date", "pk"),
    "duration": ("duration_minutes", "pk"),
}


def matches(request):
    rows = Match.objects.values(
        "id", "game_id", "match_date", "duration_minutes", "winner_id",
        "status", "is_completed", "is_scheduled").annotate(
        game_title=F("game__title"), winner_name=F("winner__name"),
        played_on=F("match_date"),
        player_count=Count("players", distinct=True))
    filter_form = MatchFilterForm(request.GET or None)
    errors = []
    sort = "date"
    if filter_form.is_bound:
        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data["q"]:
                rows = rows.filter(
                    Q(game__title__icontains=data["q"])
                    | Q(game__genre__icontains=data["q"]))
            if data["game"]:
                rows = rows.filter(game=data["game"])
            if data["player"]:
                rows = rows.filter(players=data["player"])
            if data["status"]:
                rows = rows.filter(status=data["status"])
            if data["date"]:
                rows = rows.for_date(data["date"])
            if data["from"]:
                rows = rows.filter(match_date__gte=data["from"])
            if data["to"]:
                rows = rows.filter(match_date__lte=data["to"])
            sort = data["sort"] or "date"
        else:
            rows = rows.none()
            errors = [
                str(error) for values in filter_form.errors.values()
                for error in values]
    rows = rows.order_by(*SORTS[sort])
    page = Paginator(rows, 5).get_page(request.GET.get("page"))
    return render(request, "matches/match_list.html", {
        "matches": page.object_list, "page_obj": page,
        "filter_form": filter_form, "errors": errors, "sort": sort,
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
        except IntegrityError:
            form.add_error(None, "Игра уже занята на эту дату.")
        else:
            return redirect("matches:detail", match_id=match.pk)
    return render(request, "matches/match_detail.html", {
        "match": match, "players": match.players.all(),
        "status_form": form,
        "duration_check": check_duration(match.duration_minutes)})


@require_http_methods(["GET", "POST"])
def match_edit(request, match_id=None):
    match = get_object_or_404(Match, pk=match_id) if match_id else None
    form = MatchForm(
        request.POST if request.method == "POST" else None,
        instance=match,
        initial=None if match else {"match_date": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                saved = form.save(commit=False)
                validate_availability(
                    saved.game_id, saved.match_date, saved.status, saved.pk)
                saved.save()
                form.save_m2m()
        except (IntegrityError, ValidationError):
            form.add_error(
                None, "Не удалось сохранить партию: игра занята или "
                "данные изменились. Проверьте форму.")
        else:
            messages.success(request, "Партия сохранена.")
            return redirect("matches:detail", match_id=saved.pk)
    return render(request, "matches/match_form.html", {
        "form": form, "match": match,
        "heading": "Редактировать партию" if match else "Новая партия"})


@require_POST
def match_cancel(request, match_id):
    match = get_object_or_404(Match.objects.blocking(), pk=match_id)
    match.cancel()
    messages.success(request, "Партия отменена. Запись сохранена в истории.")
    return redirect(reverse("matches:list") + "?status=active")


@require_http_methods(["GET", "POST"])
def match_delete(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == "POST":
        with transaction.atomic():
            match.delete()
        messages.success(request, "Партия удалена.")
        return redirect("matches:list")
    return render(request, "matches/match_confirm_delete.html",
                  {"match": match})


def statistics(request):
    totals = Match.objects.aggregate(
        matches_count=Count("pk"),
        completed_count=Count(
            "pk", filter=Q(status=Match.Status.COMPLETED)),
        active_count=Count("pk", filter=Q(status=Match.Status.ACTIVE)),
        scheduled_count=Count("pk", filter=Q(status=Match.Status.SCHEDULED)),
        cancelled_count=Count("pk", filter=Q(status=Match.Status.CANCELLED)),
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
                     filter=Q(matches__status__in=[
                         Match.Status.ACTIVE, Match.Status.COMPLETED])),
        wins=Count("won_matches", distinct=True, filter=Q(
            won_matches__status=Match.Status.COMPLETED))).order_by(
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
