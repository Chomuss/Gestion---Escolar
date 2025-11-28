from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Usuarios
    path("api/usuarios/", include("usuarios.urls")),

    # Académico
    path("api/academico/", include("academico.urls")),

    # API general
    path("api/core/", include("api.urls")),

    # Navegador DRF
    path("api-auth/", include("rest_framework.urls")),
]
