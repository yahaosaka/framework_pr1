from django.contrib import admin

from matches.models import MatchPlayer
from players.models import Player


class ParticipationInline(admin.TabularInline):
    model = MatchPlayer
    fields = ["match"]
    readonly_fields = ["match"]
    extra = 0
    can_delete = False
    show_change_link = False
    verbose_name_plural = "Участие в партиях"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email"]
    search_fields = ["name", "email"]
    ordering = ["name", "pk"]
    list_per_page = 10
    inlines = [ParticipationInline]
