
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from main import views as main_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("media/<path:path>", main_views.protected_media, name="protected_media")
    ]
