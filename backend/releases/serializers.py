from django.urls import reverse
from rest_framework import serializers

from .models import AppRelease


class AppReleaseSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(source="get_platform_display", read_only=True)
    notes_lines = serializers.SerializerMethodField()
    size_bytes = serializers.IntegerField(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = AppRelease
        fields = [
            "id",
            "version",
            "platform",
            "platform_display",
            "title",
            "notes",
            "notes_lines",
            "size_bytes",
            "downloads",
            "download_url",
            "created_at",
        ]

    def get_notes_lines(self, obj):
        return obj.notes_lines()

    def get_download_url(self, obj):
        url = reverse("release-download", args=[obj.pk])
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url
