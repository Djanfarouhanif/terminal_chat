from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for Hanif Chat CLI."""

    class Status(models.TextChoices):
        ONLINE = "online", "En ligne"
        OFFLINE = "offline", "Hors ligne"
        BUSY = "busy", "Occupé"
        AWAY = "away", "Absent"

    email = models.EmailField(unique=True)
    avatar = models.URLField(blank=True, default="")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OFFLINE
    )
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
