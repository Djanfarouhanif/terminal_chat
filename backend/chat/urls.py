from django.urls import path

from .views import (
    ChannelJoinView,
    ChannelLeaveView,
    ChannelListCreateView,
    DirectMessageListCreateView,
    MessageDetailView,
    MessageListCreateView,
    search,
)

urlpatterns = [
    path("channels", ChannelListCreateView.as_view(), name="channels"),
    path("channels/<int:pk>/join", ChannelJoinView.as_view(), name="channel-join"),
    path("channels/<int:pk>/leave", ChannelLeaveView.as_view(), name="channel-leave"),
    path("messages", MessageListCreateView.as_view(), name="messages"),
    path("messages/<int:pk>", MessageDetailView.as_view(), name="message-detail"),
    path("dm", DirectMessageListCreateView.as_view(), name="dm"),
    path("search", search, name="search"),
]
