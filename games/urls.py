from django.urls import path

from . import views

app_name = "games"

urlpatterns = [
    path("", views.games, name="list"),
    path("search/", views.game_search, name="search"),
    path("<int:game_id>/", views.game_detail, name="detail"),
]
