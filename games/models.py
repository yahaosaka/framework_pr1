from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from games.slugs import title_slug
from games.validators import validate_game_image


class Game(models.Model):
    image = models.ImageField(
        "Изображение", upload_to="games/%Y/%m/", blank=True,
        validators=[validate_game_image])
    slug = models.SlugField(
        "Слаг", max_length=220, unique=True, blank=True)
    title = models.CharField("Название", max_length=200, unique=True)
    min_players = models.PositiveSmallIntegerField(
        "Минимум игроков",
        validators=[MinValueValidator(2), MaxValueValidator(6)])
    max_players = models.PositiveSmallIntegerField(
        "Максимум игроков",
        validators=[MinValueValidator(2), MaxValueValidator(6)])
    genre = models.CharField("Жанр", max_length=100, blank=True)
    is_large_group = models.GeneratedField(
        expression=models.Case(
            models.When(max_players__gte=5, then=models.Value(True)),
            default=models.Value(False), output_field=models.BooleanField()),
        output_field=models.BooleanField(), db_persist=True,
        verbose_name="Для большой компании")

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"
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

    def save(self, *args, **kwargs):
        if not self.slug:
            base = title_slug(self.title) or "game"
            candidate, number = base, 2
            while type(self).objects.filter(
                    slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{number}"
                number += 1
            self.slug = candidate
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                    "slug"}
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("games:by_slug", kwargs={"slug": self.slug})
