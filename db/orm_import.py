"""Единственное новое место чтения старой SQLite напрямую."""
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction

from games.models import Game
from matches.models import Match, MatchPlayer
from players.models import Player


def import_source(source):
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError(f"Исходная база не найдена: {source}")
    with closing(sqlite3.connect(
            source.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Нарушена целостность исходной базы.")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("В исходной базе нарушены внешние ключи.")
        games = [dict(r) for r in conn.execute("SELECT * FROM games")]
        players = [dict(r) for r in conn.execute("SELECT * FROM players")]
        matches = [dict(r) for r in conn.execute("SELECT * FROM matches")]
        links = [dict(r) for r in conn.execute("SELECT * FROM match_players")]
    members = {}
    for row in links:
        members.setdefault(row["match_id"], []).append(row["player_id"])
    with transaction.atomic():
        for row in games:
            obj = Game(
                pk=row["id"], title=row["title"],
                min_players=row["min_players"], max_players=row["max_players"],
                genre=row["genre"] or "")
            obj.full_clean(validate_unique=False)
            Game.objects.update_or_create(
                pk=obj.pk, defaults={
                    field: getattr(obj, field) for field in (
                        "title", "min_players", "max_players", "genre")})
        for row in players:
            obj = Player(pk=row["id"], name=row["name"],
                         email=row["email"] or "")
            obj.full_clean(validate_unique=False)
            Player.objects.update_or_create(
                pk=obj.pk, defaults={"name": obj.name, "email": obj.email})
        for row in matches:
            ids = members.get(row["id"], [])
            game = Game.objects.get(pk=row["game_id"])
            if (len(ids) != len(set(ids))
                    or not game.min_players <= len(ids) <= game.max_players):
                raise ValidationError("Некорректный состав партии.")
            if row["is_completed"] not in (0, 1):
                raise ValidationError("Некорректный статус партии.")
            if row["winner_id"] is not None and row["winner_id"] not in ids:
                raise ValidationError("Победитель не является участником.")
            defaults = {
                "game_id": game.pk,
                "match_date": date.fromisoformat(row["match_date"]),
                "duration_minutes": row["duration_minutes"],
                "winner_id": row["winner_id"],
                "is_completed": bool(row["is_completed"]),
                "status": (Match.Status.COMPLETED if row["is_completed"]
                           else Match.Status.ACTIVE),
                "is_scheduled": False}
            # Проверяем поля до записи, состав проверен по источнику.
            candidate = Match(**defaults)
            candidate.full_clean()
            obj, _ = Match.objects.update_or_create(
                pk=row["id"], defaults=defaults)
            obj.players.set(ids)
        expected = sum(len(v) for v in members.values())
        actual = MatchPlayer.objects.filter(
            match_id__in=[r["id"] for r in matches]).count()
        if actual != expected:
            raise ValueError("Не совпало количество связей.")
    return len(games), len(players), len(matches), len(links)
