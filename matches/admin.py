from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count

from matches.admin_forms import MatchAdminForm, ParticipationFormSet
from matches.models import Match, MatchPlayer
from matches.services import change_status


class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    formset = ParticipationFormSet
    extra = 0
    autocomplete_fields = ["player"]
    verbose_name = "Участник"
    verbose_name_plural = "Участники партии"


class MatchInline(admin.TabularInline):
    model = Match
    fk_name = "game"
    fields = ["id", "match_date", "duration_minutes", "status"]
    readonly_fields = ["id", "status"]
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    form = MatchAdminForm
    list_display = [
        "id", "game", "match_date", "status", "duration_minutes",
        "participants_count", "winner"]
    list_filter = ["status", "game", "match_date"]
    search_fields = ["game__title", "players__name", "winner__name"]
    ordering = ["-match_date", "-pk"]
    list_per_page = 10
    list_select_related = ["game", "winner"]
    date_hierarchy = "match_date"
    autocomplete_fields = ["game", "winner"]
    inlines = [MatchPlayerInline]
    fields = ["game", "match_date", "duration_minutes", "status", "winner"]
    actions = ["mark_active", "mark_scheduled", "mark_cancelled"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            roster_count=Count("players", distinct=True))

    @admin.display(description="Участников", ordering="roster_count")
    def participants_count(self, obj):
        return obj.roster_count

    def _change_status(self, request, queryset, status):
        with transaction.atomic():
            for item in queryset:
                change_status(item.pk, status, None)
        self.message_user(
            request, f"Обновлено партий: {queryset.count()}",
            level=messages.SUCCESS)

    @admin.action(description="Отметить: идет")
    def mark_active(self, request, queryset):
        self._change_status(request, queryset, Match.Status.ACTIVE)

    @admin.action(description="Отметить: будет идти")
    def mark_scheduled(self, request, queryset):
        self._change_status(request, queryset, Match.Status.SCHEDULED)

    @admin.action(description="Отменить выбранные партии")
    def mark_cancelled(self, request, queryset):
        self._change_status(request, queryset, Match.Status.CANCELLED)
