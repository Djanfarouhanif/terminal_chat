from django.contrib import admin

from .models import AppRelease


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ("version", "platform", "is_published", "downloads", "created_at")
    list_filter = ("platform", "is_published")
    search_fields = ("version", "title", "notes")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("version", "platform", "title")}),
        ("Fichier", {"fields": ("file",)}),
        ("Contenu", {"fields": ("notes",)}),
        ("Publication", {"fields": ("is_published", "downloads", "created_at")}),
    )
