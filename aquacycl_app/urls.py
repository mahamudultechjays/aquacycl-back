from django.urls import path

from . import views

urlpatterns = [
    path(
        "manifest/",
        views.Manifest.as_view(),
        name="manifest",
    ),
    path(
        "manifest-history/",
        views.ManifestHistory.as_view(),
        name="manifest_history",
    ),
]
