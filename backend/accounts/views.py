from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RelayTokenObtainPairSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    serializer_class = RelayTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        username = request.data.get("username")
        if response.status_code == 200 and username:
            User.objects.filter(username=username).update(
                status=User.Status.ONLINE, last_seen=timezone.now()
            )
        return response


class LogoutView(APIView):
    def post(self, request):
        request.user.status = User.Status.OFFLINE
        request.user.last_seen = timezone.now()
        request.user.save(update_fields=["status", "last_seen"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ProfileUpdateSerializer
        return UserSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def client_version(request):
    """Dernière version publiée du client + lien de téléchargement (public)."""
    return Response(
        {
            "version": settings.CLIENT_LATEST_VERSION,
            "download_url": settings.CLIENT_DOWNLOAD_URL,
        }
    )


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by("username")

    def get_queryset(self):
        qs = super().get_queryset()
        online = self.request.query_params.get("online")
        if online in ("1", "true"):
            qs = qs.filter(status=User.Status.ONLINE)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(username__icontains=search)
        return qs
