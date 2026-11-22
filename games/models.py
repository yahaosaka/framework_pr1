from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Game(models.Model):
    title = models.CharField("Название", max_length=200, unique=True)
    min_players = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(6)])
    max_players = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(6)])
    genre = models.CharField("Жанр", max_length=100, blank=True)

    class Meta:
        ordering = ["title", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_players__gte=2)
                & models.Q(max_players__lte=6)
                & models.Q(min_players__lte=models.F("max_players")),
                name="valid_game_player_range"),
        ]

    def __str__(self):
        return self.title
