from django.urls import path

from . import views

app_name = "games"

urlpatterns = [
    path("", views.games, name="list"),
    path("<int:game_id>/", views.game_detail, name="detail"),
]
