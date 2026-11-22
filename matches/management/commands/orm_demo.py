from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from games.models import Game
from matches.models import Match
from matches.services import create_match, finish_match
from players.models import Player


class Command(BaseCommand):
    help = "Демонстрация ORM CRUD с откатом всех изменений."

    def handle(self, *args, **options):
        with transaction.atomic():
            game = Game.objects.create(
                title="__ORM CRUD demo__", min_players=2, max_players=6)
            one = Player.objects.create(name="Демо 1")
            two = Player.objects.create(name="Демо 2")
            match = create_match(game, [one, two], date.today(), 30)
            found = Match.objects.get(pk=match.pk)
            self.stdout.write(f"CREATE / GET: {found}")
            match = finish_match(match.pk, one)
            self.stdout.write(f"UPDATE: победитель {match.winner}")
            match.delete()
            one.delete()
            two.delete()
            game.delete()
            self.stdout.write("DELETE: временные объекты удалены")
            transaction.set_rollback(True)
        self.stdout.write("Транзакция отменена; исходные данные не изменены.")
