from django.urls import path

from . import views

app_name = "games"

urlpatterns = [
    path("<int:game_id>/edit/", views.game_edit, name="edit"),
    path("", views.games, name="list"),
    path("search/", views.game_search, name="search"),
    path("<int:game_id>/", views.game_detail, name="detail"),
]
