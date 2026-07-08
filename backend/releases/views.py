from django.db.models import F
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppRelease
from .serializers import AppReleaseSerializer


def _published():
    return AppRelease.objects.filter(is_published=True)


class ReleaseListView(generics.ListAPIView):
    """Liste publique des versions publiées (optionnel ?platform=windows)."""

    serializer_class = AppReleaseSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = _published()
        platform = self.request.query_params.get("platform")
        if platform:
            qs = qs.filter(platform=platform)
        return qs


class LatestReleaseView(APIView):
    """Dernière version publiée (optionnel ?platform=windows)."""

    permission_classes = [AllowAny]

    def get(self, request):
        qs = _published()
        platform = request.query_params.get("platform")
        if platform:
            qs = qs.filter(platform=platform)
        latest = qs.first()
        if latest is None:
            return Response({}, status=204)
        return Response(
            AppReleaseSerializer(latest, context={"request": request}).data
        )


class ReleaseDownloadView(APIView):
    """Sert le fichier de l'installeur et incrémente le compteur."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        release = get_object_or_404(AppRelease, pk=pk, is_published=True)
        if not release.file:
            raise Http404("Fichier indisponible.")
        AppRelease.objects.filter(pk=release.pk).update(downloads=F("downloads") + 1)
        try:
            return FileResponse(
                release.file.open("rb"),
                as_attachment=True,
                filename=release.file.name.split("/")[-1],
            )
        except FileNotFoundError:
            raise Http404("Fichier introuvable sur le serveur.")
