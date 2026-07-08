from rest_framework import serializers

from .models import Channel, DirectMessage, Message


class ChannelSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    member_count = serializers.IntegerField(source="members.count", read_only=True)
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = [
            "id",
            "name",
            "description",
            "created_by",
            "member_count",
            "is_member",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def get_is_member(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.members.filter(pk=request.user.pk).exists()


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "channel",
            "sender",
            "sender_id",
            "content",
            "edited",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sender", "edited", "created_at", "updated_at"]


class DirectMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    receiver = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = DirectMessage
        fields = [
            "id",
            "sender",
            "receiver",
            "content",
            "read",
            "created_at",
        ]
        read_only_fields = ["id", "sender", "receiver", "read", "created_at"]
