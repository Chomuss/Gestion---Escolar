from django.urls import path, include

from .views import APIRootView, MeView, HealthCheckView
from .schema import schema_view, swagger_ui_view, redoc_ui_view


urlpatterns = [
    # Root de la versión v1
    path("v1/", APIRootView.as_view(), name="api-root"),

    # Endpoints globales
    path("v1/me/", MeView.as_view(), name="api-me"),
    path("v1/health/", HealthCheckView.as_view(), name="api-health"),

    # Módulo de usuarios
    path("v1/usuarios/", include("usuarios.urls")),

    # Módulo académico
    path("v1/academico/", include("academico.urls")),

    # Schema OpenAPI
    path("schema/", schema_view, name="api-schema"),

    # Documentación interactiva
    path("docs/", swagger_ui_view, name="api-docs"),
    path("redoc/", redoc_ui_view, name="api-redoc"),
]
