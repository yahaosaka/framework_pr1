from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from games.models import Game
from matches.services import create_match
from players.models import Player


class Command(BaseCommand):
    help = "Создать подписанные тестовые данные для защиты ПР10."

    @transaction.atomic
    def handle(self, *args, **options):
        game, _ = Game.objects.get_or_create(
            title="ПР10 — демонстрационная игра",
            defaults={"min_players": 2, "max_players": 6, "genre": "учебная"})
        players = []
        for name in ("ПР10 игрок 1", "ПР10 игрок 2"):
            player = Player.objects.filter(name=name).first()
            players.append(player or Player.objects.create(name=name))
        day = date(2026, 12, 1)
        match = game.matches.filter(match_date=day).first()
        if match is None:
            match = create_match(game, players, day, 60)
        self.stdout.write(
            f"Тестовые данные: игра ID={game.pk}, партия ID={match.pk}, "
            f"дата={day}; {game.get_absolute_url()}")
        self.stdout.write(
            "Повторный запуск не сбрасывает статус существующей партии.")
