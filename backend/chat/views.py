from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Channel, DirectMessage, Message
from .serializers import (
    ChannelSerializer,
    DirectMessageSerializer,
    MessageSerializer,
)

User = get_user_model()


class ChannelListCreateView(generics.ListCreateAPIView):
    serializer_class = ChannelSerializer
    queryset = Channel.objects.all()

    def perform_create(self, serializer):
        channel = serializer.save(created_by=self.request.user)
        channel.members.add(self.request.user)


class ChannelJoinView(APIView):
    def post(self, request, pk):
        channel = generics.get_object_or_404(Channel, pk=pk)
        channel.members.add(request.user)
        return Response(ChannelSerializer(channel, context={"request": request}).data)


class ChannelLeaveView(APIView):
    def post(self, request, pk):
        channel = generics.get_object_or_404(Channel, pk=pk)
        channel.members.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        qs = Message.objects.select_related("sender")
        channel_id = self.request.query_params.get("channel")
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(content__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    queryset = Message.objects.select_related("sender")

    def perform_update(self, serializer):
        if serializer.instance.sender != self.request.user:
            self.permission_denied(self.request, message="Not your message.")
        serializer.save(edited=True)

    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
            self.permission_denied(self.request, message="Not your message.")
        instance.delete()


class DirectMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = DirectMessageSerializer

    def get_queryset(self):
        me = self.request.user
        qs = DirectMessage.objects.select_related("sender", "receiver").filter(
            Q(sender=me) | Q(receiver=me)
        )
        other = self.request.query_params.get("user")
        if other:
            qs = qs.filter(
                Q(sender__username=other) | Q(receiver__username=other)
            )
        return qs

    def perform_create(self, serializer):
        receiver = generics.get_object_or_404(
            User, username=self.request.data.get("receiver")
        )
        serializer.save(sender=self.request.user, receiver=receiver)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search(request):
    """Unified search across users, channels and messages."""
    q = request.query_params.get("q", "").strip()
    if not q:
        return Response({"users": [], "channels": [], "messages": []})

    from accounts.serializers import UserSerializer

    users = User.objects.filter(username__icontains=q)[:20]
    channels = Channel.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q)
    )[:20]
    messages = Message.objects.select_related("sender").filter(
        content__icontains=q
    )[:20]

    return Response(
        {
            "users": UserSerializer(users, many=True).data,
            "channels": ChannelSerializer(
                channels, many=True, context={"request": request}
            ).data,
            "messages": MessageSerializer(messages, many=True).data,
        }
    )
