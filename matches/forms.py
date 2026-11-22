from django import forms

from games.models import Game
from matches.models import Match
from players.models import Player


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Статус", choices=Match.Status.choices)
    winner = forms.ModelChoiceField(
        label="Победитель", queryset=Player.objects.none(), required=False,
        empty_label="Не выбран")

    def __init__(self, *args, match, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["winner"].queryset = match.players.all()
        self.fields["winner"].choices = [
            ("", "Не выбран"),
            *((player.pk, str(player)) for player in match.players.all())]
        if not self.is_bound:
            self.initial.update(
                status=match.status,
                winner=match.winner_id)

    def clean(self):
        data = super().clean()
        if (data.get("status") == Match.Status.COMPLETED
                and not data.get("winner")):
            self.add_error("winner", "Выберите победителя из участников.")
        if data.get("status") != Match.Status.COMPLETED:
            data["winner"] = None
        return data


class MatchForm(forms.Form):
    game = forms.ModelChoiceField(label="Игра", queryset=Game.objects.all())
    players = forms.ModelMultipleChoiceField(
        label="Участники", queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple)
    match_date = forms.DateField(
        label="Дата", widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"])
    duration_minutes = forms.IntegerField(
        label="Продолжительность, минут", min_value=1, max_value=2147483647)
    status = forms.ChoiceField(
        label="Статус", choices=Match.Status.choices, initial="active")
    winner = forms.ModelChoiceField(
        label="Победитель", queryset=Player.objects.all(), required=False,
        empty_label="Не выбран",
        help_text="Для завершенной партии выберите одного из участников.")

    def clean(self):
        data = super().clean()
        game, players = data.get("game"), data.get("players")
        if game and players is not None:
            if not game.min_players <= len(players) <= game.max_players:
                self.add_error(
                    "players", f"Для этой игры нужно от {game.min_players} "
                    f"до {game.max_players} участников.")
        if data.get("status") != Match.Status.COMPLETED:
            data["winner"] = None
        elif data.get("status") == Match.Status.COMPLETED:
            winner = data.get("winner")
            if not winner:
                self.add_error("winner", "Выберите победителя.")
            elif players is not None and winner not in players:
                self.add_error("winner", "Победитель должен быть участником.")
        return data
