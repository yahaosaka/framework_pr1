"""Операции записи ORM; доступны из shell и management-команд."""
from django.core.exceptions import ValidationError
from django.db import transaction

from matches.models import Match


@transaction.atomic
def save_match(*, game, players, match_date, duration_minutes,
               is_completed=False, winner=None, match_id=None, status=None):
    """Проверить предложенное состояние и сохранить целиком."""
    if status is None:
        status = "completed" if is_completed else "active"
    if status not in Match.Status.values:
        raise ValidationError("Неизвестный статус.")
    is_completed = status == Match.Status.COMPLETED
    players = list(players)
    ids = [player.pk for player in players]
    if (len(ids) != len(set(ids)) or any(pk is None for pk in ids)
            or not game.min_players <= len(ids) <= game.max_players):
        raise ValidationError("Некорректный состав участников.")
    if not is_completed:
        winner = None
    if is_completed and (winner is None or winner.pk not in ids):
        raise ValidationError("Выберите победителя из участников.")
    candidate = Match(
        game=game, match_date=match_date, duration_minutes=duration_minutes,
        is_completed=is_completed, is_scheduled=status == "scheduled",
        winner=winner)
    candidate.full_clean()
    if match_id is None:
        match = candidate
    else:
        match = Match.objects.select_for_update().get(pk=match_id)
        for field in (
                "game", "match_date", "duration_minutes",
                "is_completed", "is_scheduled", "winner"):
            setattr(match, field, getattr(candidate, field))
    match.save()
    match.players.set(players)
    return match


@transaction.atomic
def change_status(match_id, status, winner):
    if status not in Match.Status.values:
        raise ValidationError("Неизвестный статус.")
    is_completed = status == Match.Status.COMPLETED
    match = Match.objects.select_for_update().get(pk=match_id)
    if not is_completed:
        winner = None
    elif winner is None or not match.players.filter(pk=winner.pk).exists():
        raise ValidationError("Выберите победителя из участников.")
    match.is_completed = is_completed
    match.is_scheduled = status == Match.Status.SCHEDULED
    match.winner = winner
    match.full_clean()
    match.save(update_fields=["is_completed", "is_scheduled", "winner"])
    return match


@transaction.atomic
def create_match(game, players, match_date, duration_minutes):
    players = list(players)
    ids = [player.pk for player in players]
    if len(ids) != len(set(ids)) or any(pk is None for pk in ids):
        raise ValidationError("Участники должны быть сохранены и уникальны.")
    if not game.min_players <= len(ids) <= game.max_players:
        raise ValidationError("Число участников не подходит для игры.")
    match = Match(game=game, match_date=match_date,
                  duration_minutes=duration_minutes)
    match.full_clean()
    match.save()
    match.players.set(players)
    return match


@transaction.atomic
def finish_match(match_id, winner):
    match = Match.objects.select_for_update().get(pk=match_id)
    if match.is_completed:
        raise ValidationError("Партия уже завершена.")
    if not match.players.filter(pk=winner.pk).exists():
        raise ValidationError("Победитель должен участвовать в партии.")
    changed = Match.objects.filter(
        pk=match_id, is_completed=False).update(
        winner=winner, is_completed=True, is_scheduled=False)
    if not changed:
        raise ValidationError("Партия уже завершена.")
    match.refresh_from_db()
    return match
