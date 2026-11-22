from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from matches.querysets import MatchQuerySet


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Будет идти"
        ACTIVE = "active", "Идет"
        COMPLETED = "completed", "Завершена"
        CANCELLED = "cancelled", "Отменена"

    status = models.CharField(
        "Статус", max_length=12, choices=Status.choices,
        default=Status.ACTIVE)
    objects = MatchQuerySet.as_manager()

    game = models.ForeignKey(
        "games.Game", on_delete=models.PROTECT, related_name="matches",
        verbose_name="Игра")
    match_date = models.DateField("Дата")
    duration_minutes = models.PositiveIntegerField(
        "Продолжительность, минут",
        validators=[MinValueValidator(1)])
    players = models.ManyToManyField(
        "players.Player", through="MatchPlayer", related_name="matches",
        verbose_name="Участники")
    winner = models.ForeignKey(
        "players.Player", null=True, blank=True, on_delete=models.PROTECT,
        related_name="won_matches", verbose_name="Победитель")
    is_completed = models.BooleanField(default=False, editable=False)
    is_scheduled = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = "Партия"
        verbose_name_plural = "Партии"
        ordering = ["match_date", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(status="completed", is_completed=True,
                             is_scheduled=False)
                    | models.Q(status="scheduled", is_completed=False,
                               is_scheduled=True)
                    | models.Q(status__in=["active", "cancelled"],
                               is_completed=False, is_scheduled=False)),
                name="match_status_flags_consistent"),
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
        self.sync_status_flags()
        if self.is_completed != (self.winner_id is not None):
            raise ValidationError("Статус не соответствует победителю.")
        if (not getattr(self, "_defer_roster_validation", False)
                and self.pk and self.winner_id and not self.players.filter(
                    pk=self.winner_id).exists()):
            raise ValidationError("Победитель должен участвовать в партии.")

    def sync_status_flags(self):
        self.is_completed = self.status == self.Status.COMPLETED
        self.is_scheduled = self.status == self.Status.SCHEDULED

    def save(self, *args, **kwargs):
        self.sync_status_flags()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                "status", "is_completed", "is_scheduled"}
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("matches:detail", kwargs={"match_id": self.pk})

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
        Match, on_delete=models.CASCADE, related_name="participations",
        verbose_name="Партия")
    player = models.ForeignKey(
        "players.Player", on_delete=models.PROTECT,
        related_name="participations", verbose_name="Игрок")

    class Meta:
        verbose_name = "Участие"
        verbose_name_plural = "Участники партий"
        constraints = [
            models.UniqueConstraint(
                fields=["match", "player"], name="unique_match_player"),
        ]
