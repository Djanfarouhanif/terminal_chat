from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Relay — Administration"
admin.site.site_title = "Relay Admin"
admin.site.index_title = "Gestion"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls_auth")),
    path("api/", include("accounts.urls")),
    path("api/", include("chat.urls")),
    path("api/", include("releases.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
