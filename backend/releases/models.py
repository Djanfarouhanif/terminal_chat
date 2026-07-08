from django.db import models


class AppRelease(models.Model):
    class Platform(models.TextChoices):
        WINDOWS = "windows", "Windows"
        LINUX = "linux", "Linux"
        MACOS = "macos", "macOS"
        SOURCE = "source", "Code source"

    version = models.CharField("Version", max_length=32, help_text="ex. 0.1.0")
    platform = models.CharField(
        "Plateforme", max_length=16, choices=Platform.choices, default=Platform.WINDOWS
    )
    title = models.CharField("Titre (facultatif)", max_length=120, blank=True, default="")
    notes = models.TextField(
        "Notes de version", blank=True, default="",
        help_text="Nouveautés / corrections (une ligne par point).",
    )
    file = models.FileField("Fichier (installeur)", upload_to="releases/")
    is_published = models.BooleanField(
        "Publiée", default=True,
        help_text="Décocher pour préparer une version sans la rendre visible.",
    )
    downloads = models.PositiveIntegerField("Téléchargements", default=0, editable=False)
    created_at = models.DateTimeField("Ajoutée le", auto_now_add=True)

    class Meta:
        verbose_name = "version de l'application"
        verbose_name_plural = "versions de l'application"
        ordering = ["-created_at"]
        unique_together = ("version", "platform")

    def __str__(self):
        return f"{self.get_platform_display()} v{self.version}"

    @property
    def size_bytes(self):
        try:
            return self.file.size
        except (ValueError, OSError):
            return None

    def notes_lines(self):
        return [ln.strip() for ln in self.notes.splitlines() if ln.strip()]
