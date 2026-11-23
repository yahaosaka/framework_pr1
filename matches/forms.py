from django import forms
from django.utils import timezone

from games.models import Game
from homepage.form_widgets import BootstrapFormMixin
from matches.models import Match
from matches.validators import validate_duration
from players.models import Player

SORT_CHOICES = [
    ("date", "По дате"), ("-date", "Новые первыми"),
    ("game", "По игре и дате"), ("duration", "По длительности")]


class MatchFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        label="Название игры или жанр", required=False, max_length=200)
    game = forms.ModelChoiceField(
        label="Игра", queryset=Game.objects.all(), required=False,
        empty_label="Все игры")
    player = forms.ModelChoiceField(
        label="Игрок", queryset=Player.objects.all(), required=False,
        empty_label="Все игроки")
    status = forms.ChoiceField(
        label="Статус", required=False,
        choices=[("", "Все статусы"), *Match.Status.choices])
    date = forms.DateField(
        label="Точная дата", required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    sort = forms.ChoiceField(
        label="Порядок", choices=SORT_CHOICES, required=False, initial="date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сохраняем прежние URL-параметры from/to.
        for name, label in (("from", "С даты"), ("to", "По дату")):
            self.fields[name] = forms.DateField(
                label=label, required=False,
                widget=forms.DateInput(
                    format="%Y-%m-%d",
                    attrs={"type": "date", "class": "form-control"}))

    def clean(self):
        data = super().clean()
        start, end = data.get("from"), data.get("to")
        if start and end and start > end:
            raise forms.ValidationError("Начало периода позже окончания.")
        return data


class StatusForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(label="Статус", choices=Match.Status.choices)
    winner = forms.ModelChoiceField(
        label="Победитель", queryset=Player.objects.none(), required=False,
        empty_label="Не выбран",
        help_text="Нужен только для завершенной партии.")

    def __init__(self, *args, match, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["winner"].queryset = match.players.all()
        self.fields["winner"].choices = [
            ("", "Не выбран"),
            *((player.pk, str(player)) for player in match.players.all())]
        if not self.is_bound:
            self.initial.update(status=match.status, winner=match.winner_id)

    def clean(self):
        data = super().clean()
        if (data.get("status") == Match.Status.COMPLETED
                and not data.get("winner")):
            self.add_error("winner", "Выберите победителя из участников.")
        if data.get("status") != Match.Status.COMPLETED:
            data["winner"] = None
        return data


class MatchForm(BootstrapFormMixin, forms.ModelForm):
    duration_minutes = forms.IntegerField(
        label="Продолжительность, минут", min_value=1,
        validators=[validate_duration],
        help_text="От 1 до 1440 минут; свыше 240 — длительная партия.")

    class Meta:
        model = Match
        fields = [
            "game", "players", "match_date", "duration_minutes",
            "status", "winner", "notes"]
        labels = {"match_date": "Дата партии", "notes": "Примечание"}
        help_texts = {
            "game": "Один экземпляр игры — одна занятая партия в день.",
            "players": "Отметьте участников, подходящих для выбранной игры.",
            "match_date": "Для новой партии — сегодня или будущая дата.",
            "winner": "Для завершенной партии выберите участника.",
            "notes": "Необязательно, до 1000 символов."}
        widgets = {
            "match_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}),
            "players": forms.CheckboxSelectMultiple,
            "notes": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Заметки о партии"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_date = self.instance.match_date
        # Новый состав проверяется формой, а не по старым связям в базе.
        self.instance._defer_roster_validation = True

    def clean_match_date(self):
        value = self.cleaned_data["match_date"]
        # Историческую дату разрешено оставить прежней.
        unchanged_history = self.instance.pk and value == self.original_date
        if value < timezone.localdate() and not unchanged_history:
            raise forms.ValidationError(
                "Нельзя назначить партию на прошедшую дату.")
        return value

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
        elif not data.get("winner"):
            self.add_error("winner", "Выберите победителя.")
        elif players is not None and data["winner"] not in players:
            self.add_error("winner", "Победитель должен быть участником.")
        return data
