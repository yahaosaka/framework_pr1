from django.urls import path

from . import views

app_name = "matches"

urlpatterns = [
    path("", views.matches, name="list"),
    path("<int:match_id>/", views.match_detail, name="detail"),
]
