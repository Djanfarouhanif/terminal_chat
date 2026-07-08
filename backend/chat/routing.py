from django.urls import re_path

from .consumers import ChatConsumer, DMConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<channel_name>[\w-]+)/$", ChatConsumer.as_asgi()),
    re_path(r"^ws/dm/$", DMConsumer.as_asgi()),
]
