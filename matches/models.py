from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Будет идти"
        ACTIVE = "active", "Идет"
        COMPLETED = "completed", "Завершена"

    game = models.ForeignKey(
        "games.Game", on_delete=models.PROTECT, related_name="matches")
    match_date = models.DateField("Дата")
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)])
    players = models.ManyToManyField(
        "players.Player", through="MatchPlayer", related_name="matches")
    winner = models.ForeignKey(
        "players.Player", null=True, blank=True, on_delete=models.PROTECT,
        related_name="won_matches")
    is_completed = models.BooleanField(default=False)
    is_scheduled = models.BooleanField(default=False)

    class Meta:
        ordering = ["match_date", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(is_scheduled=True, is_completed=True),
                name="scheduled_match_not_completed"),
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gt=0),
                name="positive_match_duration"),
            models.CheckConstraint(
                condition=(
                    models.Q(is_completed=False, winner__isnull=True)
                    | models.Q(is_completed=True, winner__isnull=False)),
                name="consistent_match_result"),
        ]

    def clean(self):
        super().clean()
        if self.is_completed != (self.winner_id is not None):
            raise ValidationError("Статус не соответствует победителю.")
        if self.pk and self.winner_id and not self.players.filter(
                pk=self.winner_id).exists():
            raise ValidationError("Победитель должен участвовать в партии.")

    @property
    def status(self):
        if self.is_completed:
            return self.Status.COMPLETED
        if self.is_scheduled:
            return self.Status.SCHEDULED
        return self.Status.ACTIVE

    def get_status_display(self):
        return self.Status(self.status).label

    @property
    def played_on(self):
        return self.match_date

    @property
    def duration_hours(self):
        return round(self.duration_minutes / 60, 1)

    @property
    def game_title(self):
        return self.game.title

    @property
    def winner_name(self):
        return self.winner.name if self.winner else ""

    def __str__(self):
        return f"Партия №{self.pk}: {self.game} ({self.match_date})"


class MatchPlayer(models.Model):
    match = models.ForeignKey(
        Match, on_delete=models.CASCADE, related_name="participations")
    player = models.ForeignKey(
        "players.Player", on_delete=models.PROTECT,
        related_name="participations")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["match", "player"], name="unique_match_player"),
        ]
