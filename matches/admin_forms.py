from django import forms
from django.forms.models import BaseInlineFormSet

from matches.models import Match


class MatchAdminForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Состав из inline проверяется после основной формы.
        self.instance._defer_roster_validation = True

    def clean(self):
        data = super().clean()
        if data.get("status") != Match.Status.COMPLETED:
            data["winner"] = None
        elif not data.get("winner"):
            self.add_error("winner", "Для завершения выберите победителя.")
        return data


class ParticipationFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        participants = []
        for form in self.forms:
            data = getattr(form, "cleaned_data", {})
            if data and not data.get("DELETE") and data.get("player"):
                participants.append(data["player"].pk)
        match = self.instance
        if not match.game_id:
            return
        if not match.game.min_players <= len(participants) <= (
                match.game.max_players):
            raise forms.ValidationError(
                f"Для игры нужно от {match.game.min_players} "
                f"до {match.game.max_players} участников.")
        if match.winner_id and match.winner_id not in participants:
            raise forms.ValidationError(
                "Победитель должен входить в выбранный состав.")
