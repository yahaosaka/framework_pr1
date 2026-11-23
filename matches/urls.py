from django.urls import path

from . import views

app_name = "matches"

urlpatterns = [
    path("", views.matches, name="list"),
    path("statistics/", views.statistics, name="statistics"),
    path("new/", views.match_edit, name="create"),
    path("<int:match_id>/cancel/", views.match_cancel, name="cancel"),
    path("<int:match_id>/delete/", views.match_delete, name="delete"),
    path("<int:match_id>/edit/", views.match_edit, name="edit"),
    path("<int:match_id>/", views.match_detail, name="detail"),
]
