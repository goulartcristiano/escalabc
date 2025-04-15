# core/urls.py
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.urls import path, include  # Importe include
from django.shortcuts import redirect  # Importe redirect para a raiz
from django.conf import settings
from django.conf.urls.static import static  # Importe static

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="login", permanent=False),
        name="root-redirect",
    ),
    path("admin/", admin.site.urls),
    path("", include("usuarios.urls")),
    path("escala/", include("escala.urls", namespace="escala")),
]

# Adicione esta linha para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
