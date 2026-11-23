from django.urls import path

from . import views

app_name = "games"

urlpatterns = [
    path("new/", views.game_edit, name="create"),
    path("available/", views.available_games, name="available"),
    path("by-slug/<slug:slug>/", views.game_detail, name="by_slug"),
    path("<int:game_id>/edit/", views.game_edit, name="edit"),
    path("", views.games, name="list"),
    path("search/", views.game_search, name="search"),
    path("<int:game_id>/", views.game_detail, name="detail"),
]
