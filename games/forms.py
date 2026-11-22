from django import forms

from games.models import Game


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ["title", "min_players", "max_players", "genre"]
        labels = {
            "min_players": "Минимум игроков",
            "max_players": "Максимум игроков"}
