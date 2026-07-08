from django.urls import path

from .views import ProfileView, UserListView, client_version

urlpatterns = [
    path("profile", ProfileView.as_view(), name="profile"),
    path("users", UserListView.as_view(), name="users"),
    path("client-version", client_version, name="client-version"),
]
