# usuarios/middleware.py

from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone


class SecurityAuditMiddleware:
    """
    Middleware de seguridad y auditoría automática para la API de gestión escolar.

    Funciones principales:
    - Bloquear usuarios marcados como bloqueados o con bloqueo temporal.
    - Forzar cambio de contraseña si must_change_password = True.
    - Registrar automáticamente acciones de escritura (POST, PUT, PATCH, DELETE)
      en el log de actividad (UserActivityLog).
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Rutas permitidas aunque el usuario deba cambiar contraseña
        # (ajusta según el prefijo que uses en urls.py principal)
        self.allowed_when_must_change_password = {
            "/api/usuarios/auth/login/",
            "/api/usuarios/auth/logout/",
            "/api/usuarios/usuarios/me/cambiar-password/",
        }

    def __call__(self, request):
        """
        Fase pre + post de la request.
        """

        # Pre: validaciones de seguridad
        response = self._process_security(request)
        if response is not None:
            # Si hay respuesta aquí, se corta el flujo.
            return response

        # Marcar si debemos auditar esta petición
        self._mark_for_audit(request)

        # Ejecutar la vista / resto del stack
        response = self.get_response(request)

        # Post: auditoría automática
        self._process_audit(request, response)

        return response

    # ============================================================
    #  SEGURIDAD
    # ============================================================

    def _process_security(self, request):
        """
        Revisa condiciones de seguridad antes de llegar a la vista.
        - Bloqueo de usuarios.
        - Obligación de cambio de contraseña.
        """

        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return None  # Usuarios no autenticados siguen flujo normal

        # Import local para evitar problemas en migraciones
        from .models import User  # noqa

        # Asegurarse de trabajar con el modelo correcto
        if not isinstance(user, User):
            return None

        path = request.path

        # 1) Bloqueo por bandera is_blocked o bloqueo temporal
        if getattr(user, "is_blocked", False) or (
            hasattr(user, "is_temporarily_blocked") and user.is_temporarily_blocked()
        ):
            return JsonResponse(
                {
                    "detail": "Usuario bloqueado. Contacte al administrador.",
                    "code": "user_blocked",
                },
                status=403,
            )

        # 2) Debe cambiar contraseña antes de usar el sistema
        if getattr(user, "must_change_password", False):
            if path not in self.allowed_when_must_change_password:
                return JsonResponse(
                    {
                        "detail": "Debe cambiar su contraseña antes de continuar.",
                        "code": "password_change_required",
                    },
                    status=403,
                )

        return None

    # ============================================================
    #  MARCA PARA AUDITORÍA
    # ============================================================

    def _mark_for_audit(self, request):
        """
        Marca la petición si debe ser auditada automáticamente.
        Auditamos solo métodos que modifican estado:
        - POST
        - PUT
        - PATCH
        - DELETE
        """

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Bandera para usar luego en _process_audit
            setattr(request, "_should_audit", True)
        else:
            setattr(request, "_should_audit", False)

    # ============================================================
    #  AUDITORÍA AUTOMÁTICA
    # ============================================================

    def _process_audit(self, request, response):
        """
        Registra automáticamente en UserActivityLog las acciones
        de escritura realizadas por usuarios autenticados.
        """

        user = getattr(request, "user", None)
        should_audit = getattr(request, "_should_audit", False)

        if not should_audit:
            return

        if not user or not user.is_authenticated:
            return

        # Evitar registrar auditoría de login (ya lo hacemos en la vista)
        path = request.path
        if path in ("/api/usuarios/auth/login/", "/api/usuarios/auth/logout/"):
            return

        try:
            from .models import UserActivityLog  # import local

            UserActivityLog.objects.create(
                user=user,
                action=f"{request.method} {path}",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.headers.get("User-Agent", ""),
            )
        except Exception:
            # En producción podrías loguear esto con logging, aquí lo silenciamos
            pass
