from django.contrib import admin

from games.forms import GameForm
from games.models import Game
from matches.admin import MatchInline


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameForm
    list_display = [
        "id", "title", "genre", "min_players", "max_players", "large_company"]
    list_filter = ["genre", "is_large_group"]
    search_fields = ["title", "genre"]
    ordering = ["title", "pk"]
    list_per_page = 10
    readonly_fields = ["large_company"]
    fields = [
        "title", "slug", "genre", "min_players", "max_players",
        "large_company", "image"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [MatchInline]

    @admin.display(description="Для большой компании", boolean=True,
                   ordering="is_large_group")
    def large_company(self, obj):
        return obj.is_large_group
