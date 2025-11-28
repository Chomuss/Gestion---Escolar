# api/views.py

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse

from django.contrib.auth import get_user_model

from academico.serializers import UsuarioSimpleSerializer

User = get_user_model()


class APIRootView(APIView):
    """
    Raíz de la API v1.

    Entrega información básica y enlaces a los módulos principales.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        base = request.build_absolute_uri("/")  # ej: http://localhost:8000/
        api_base = request.build_absolute_uri(reverse("api-root"))  # /api/v1/

        def _url(path: str) -> str:
            if path.startswith("/"):
                path = path[1:]
            return f"{base}{path}"

        data = {
            "name": "Gestión Escolar API",
            "version": "v1",
            "api_root": api_base,
            "resources": {
                "me": request.build_absolute_uri(reverse("api-me")),
                "health": request.build_absolute_uri(reverse("api-health")),
                "usuarios": _url("api/v1/usuarios/"),
                "academico": _url("api/v1/academico/"),
                "schema": _url("api/schema/"),
                "docs_swagger": _url("api/docs/"),
                "docs_redoc": _url("api/redoc/"),
            },
        }
        return Response(data)


class MeView(APIView):
    """
    Devuelve información del usuario autenticado.

    GET /api/v1/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UsuarioSimpleSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class HealthCheckView(APIView):
    """
    Endpoint simple para verificar que la API está viva.

    GET /api/v1/health/
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        data = {
            "status": "ok",
            "time": now.isoformat(),
            "version": "v1",
        }
        return Response(data)
