from django import forms
from django.db import models
from django.db.models import Count

from games.models import Game


class GameForm(forms.ModelForm):
    def clean_slug(self):
        value = self.cleaned_data.get("slug")
        return value or self.instance.slug

    class Meta:
        model = Game
        fields = ["title", "slug", "min_players", "max_players", "genre"]
        labels = {
            "min_players": "Минимум игроков",
            "max_players": "Максимум игроков"}

    def clean(self):
        data = super().clean()
        minimum, maximum = data.get("min_players"), data.get("max_players")
        if self.instance.pk and minimum and maximum:
            counts = self.instance.matches.annotate(n=Count("players"))
            invalid = counts.filter(
                models.Q(n__lt=minimum) | models.Q(n__gt=maximum))
            if invalid.exists():
                raise forms.ValidationError(
                    "Новый диапазон несовместим с существующими партиями.")
        return data
