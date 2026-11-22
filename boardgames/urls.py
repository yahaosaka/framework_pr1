"""Корневая маршрутизация проекта."""

from django.contrib import admin
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("games/", include("games.urls")),
    path("matches/", include("matches.urls")),
]

handler404 = "homepage.views.page_not_found"

if settings.DEBUG and not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
