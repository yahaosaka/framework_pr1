from pathlib import Path
from sqlite3 import Error as SQLiteError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from db.orm_import import import_source


class Command(BaseCommand):
    help = "Перенести данные ПР7 в ORM, сохранив ID и связи."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", type=Path,
            default=settings.BASE_DIR / "data" / "boardgames.sqlite")

    def handle(self, *args, **options):
        source = options["source"].resolve()
        if source == Path(settings.DATABASES["default"]["NAME"]).resolve():
            raise CommandError("Источник и целевая база должны различаться.")
        try:
            counts = import_source(source)
        except (ValueError, ValidationError,
                DatabaseError, SQLiteError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            "Перенесено: игры=%s, игроки=%s, партии=%s, связи=%s" % counts))
