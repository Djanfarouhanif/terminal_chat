from django.urls import path

from .views import LatestReleaseView, ReleaseDownloadView, ReleaseListView

urlpatterns = [
    path("releases", ReleaseListView.as_view(), name="release-list"),
    path("releases/latest", LatestReleaseView.as_view(), name="release-latest"),
    path("releases/<int:pk>/download", ReleaseDownloadView.as_view(), name="release-download"),
]
