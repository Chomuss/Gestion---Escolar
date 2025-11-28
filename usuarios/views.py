from django.utils.dateparse import parse_datetime
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import (
    User,
    Role,
    CustomPermission,
    UserGroup,
    Notification,
    UserActivityLog,
)
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    RoleSerializer,
    CustomPermissionSerializer,
    UserGroupSerializer,
    NotificationSerializer,
    ActivityLogSerializer,
)
from .permissions import (
    IsAdminRole,
    IsInstitutionalStaff,
    IsOwnerOrAdmin,
    IsActiveUser,
)


# ============================================================
#  HELPER PARA LOGS DE ACTIVIDAD
# ============================================================

def crear_log_actividad(actor: User, accion: str, request=None):
    """
    Registra acciones relevantes realizadas por usuarios.
    """
    ip = None
    ua = ""
    if request is not None:
        ip = request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT", "")

    # Si aún no hay actor (por algún contexto extraño) no registrar
    if actor and actor.is_authenticated:
        UserActivityLog.objects.create(
            user=actor,
            action=accion,
            ip_address=ip,
            user_agent=ua,
        )


# ============================================================
#  USER VIEWSET (CRUD + ACCIONES ESPECIALES)
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    Gestión completa de usuarios institucionales.

    Acciones estándar:
    - list      (GET /api/usuarios/)                  -> ADMIN/DIRECTOR
    - create    (POST /api/usuarios/)                 -> ADMIN/DIRECTOR
    - retrieve  (GET /api/usuarios/{id}/)             -> dueño o ADMIN
    - update    (PUT /api/usuarios/{id}/)             -> dueño o ADMIN
    - partial_update (PATCH /api/usuarios/{id}/)      -> dueño o ADMIN
    - destroy   (DELETE /api/usuarios/{id}/)          -> solo ADMIN, respetando jerarquía

    Acciones extra:
    - me                        (GET  /api/usuarios/me/)
    - change-password           (POST /api/usuarios/change-password/)
    - bloquear                  (POST /api/usuarios/{id}/bloquear/)
    - desbloquear               (POST /api/usuarios/{id}/desbloquear/)
    - reset-password            (POST /api/usuarios/{id}/reset-password/)
    - force-password-change     (POST /api/usuarios/{id}/force-password-change/)
    - asignar-apoderados        (POST /api/usuarios/{id}/asignar-apoderados/)
    - asignar-alumnos           (POST /api/usuarios/{id}/asignar-alumnos/)
    - actividad                 (GET  /api/usuarios/{id}/actividad/)
    """

    queryset = User.objects.select_related("role").prefetch_related(
        "groups_institutional", "extra_permissions", "alumnos", "apoderados"
    ).order_by("username")

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "first_name", "last_name", "rut", "email"]
    ordering_fields = ["username", "first_name", "last_name", "created_at"]
    ordering = ["username"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Permisos por acción.
        """
        if self.action in ["list", "create"]:
            perms = [permissions.IsAuthenticated, IsInstitutionalStaff, IsActiveUser]
        elif self.action in [
            "destroy",
            "bloquear",
            "desbloquear",
            "reset_password",
            "force_password_change",
            "asignar_apoderados",
            "asignar_alumnos",
            "actividad",
        ]:
            perms = [permissions.IsAuthenticated, IsAdminRole, IsActiveUser]
        elif self.action in ["retrieve", "update", "partial_update"]:
            # Dueño o admin
            perms = [permissions.IsAuthenticated, IsOwnerOrAdmin, IsActiveUser]
        elif self.action in ["me", "change_password"]:
            perms = [permissions.IsAuthenticated, IsActiveUser]
        else:
            perms = [permissions.IsAuthenticated, IsActiveUser]
        return [p() for p in perms]

    # --------------------------------------------------------
    # HOOKS DE CREACIÓN / ACTUALIZACIÓN / ELIMINACIÓN
    # --------------------------------------------------------

    def perform_create(self, serializer):
        user = serializer.save()
        crear_log_actividad(self.request.user, f"Creación de usuario {user.username}", self.request)

    def perform_update(self, serializer):
        user = serializer.save()
        crear_log_actividad(self.request.user, f"Actualización de usuario ID {user.id}", self.request)

    def perform_destroy(self, instance):
        req_user = self.request.user

        if req_user.role and instance.role:
            # Jerarquía: número menor = más poder
            if req_user.role.hierarchy > instance.role.hierarchy:
                raise PermissionDenied("No puedes eliminar a un usuario con mayor jerarquía.")

        crear_log_actividad(req_user, f"Eliminación de usuario ID {instance.id}", self.request)
        instance.delete()

    # --------------------------------------------------------
    #  /me
    # --------------------------------------------------------

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """
        Devuelve el perfil del usuario autenticado.
        """
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    # --------------------------------------------------------
    #  change-password (usuario cambia SU propia contraseña)
    # --------------------------------------------------------

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        """
        Permite al usuario autenticado cambiar su contraseña.

        Body:
        {
            "old_password": "...",
            "new_password": "..."
        }
        """
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"detail": "Debe proporcionar 'old_password' y 'new_password'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            return Response(
                {"detail": "La contraseña actual no es correcta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response(
                {"detail": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.must_change_password = False
        user.save()

        crear_log_actividad(user, "Cambio de contraseña propio.", request)
        return Response({"detail": "Contraseña actualizada correctamente."}, status=status.HTTP_200_OK)

    # --------------------------------------------------------
    #  BLOQUEAR / DESBLOQUEAR
    # --------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="bloquear")
    def bloquear(self, request, pk=None):
        """
        Bloquea a un usuario.
        Opcional:
        - blocked_until: fecha/hora en formato ISO 8601
        """
        user = self.get_object()

        if user.id == request.user.id:
            return Response(
                {"detail": "No puedes bloquear tu propia cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar jerarquía
        if request.user.role and user.role:
            if request.user.role.hierarchy > user.role.hierarchy:
                return Response(
                    {"detail": "No puedes bloquear a un usuario con mayor jerarquía."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        blocked_until_str = request.data.get("blocked_until")
        if blocked_until_str:
            dt = parse_datetime(blocked_until_str)
            if not dt:
                return Response(
                    {"detail": "Formato de fecha inválido para 'blocked_until'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.blocked_until = dt

        user.is_blocked = True
        user.save()

        crear_log_actividad(request.user, f"Usuario ID {user.id} bloqueado.", request)
        return Response({"detail": "Usuario bloqueado correctamente."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="desbloquear")
    def desbloquear(self, request, pk=None):
        """
        Desbloquea a un usuario.
        """
        user = self.get_object()

        user.is_blocked = False
        user.blocked_until = None
        user.save()

        crear_log_actividad(request.user, f"Usuario ID {user.id} desbloqueado.", request)
        return Response({"detail": "Usuario desbloqueado correctamente."}, status=status.HTTP_200_OK)

    # --------------------------------------------------------
    #  RESET PASSWORD / FORCE PASSWORD CHANGE
    # --------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        """
        Reinicia la contraseña de un usuario.
        Solo ADMIN.

        Body:
        {
            "new_password": "..."
        }
        """
        user = self.get_object()
        new_password = request.data.get("new_password")

        if user.id == request.user.id:
            return Response(
                {"detail": "No puedes reiniciar tu propia contraseña usando este endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_password:
            return Response(
                {"detail": "Debes proporcionar 'new_password'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response(
                {"detail": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.must_change_password = True
        user.save()

        crear_log_actividad(request.user, f"Reset de contraseña de usuario ID {user.id}.", request)
        return Response({"detail": "Contraseña restablecida correctamente."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="force-password-change")
    def force_password_change(self, request, pk=None):
        """
        Marca al usuario para que deba cambiar su contraseña
        en el próximo inicio de sesión.
        """
        user = self.get_object()
        user.must_change_password = True
        user.save()

        crear_log_actividad(
            request.user,
            f"Marcado cambio obligatorio de contraseña para usuario ID {user.id}.",
            request,
        )

        return Response(
            {"detail": "Se ha forzado el cambio de contraseña para este usuario."},
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------------
    #  ASIGNAR APODERADOS / ALUMNOS
    # --------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="asignar-apoderados")
    def asignar_apoderados(self, request, pk=None):
        """
        Asigna apoderados a un alumno.

        Body:
        {
            "apoderado_ids": [1, 2, 3]
        }
        """
        alumno = self.get_object()

        if not (alumno.role and alumno.role.code == "ALUMNO"):
            return Response(
                {"detail": "Solo puedes asignar apoderados a usuarios con rol ALUMNO."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        apoderado_ids = request.data.get("apoderado_ids", [])
        if not isinstance(apoderado_ids, list):
            return Response(
                {"detail": "apoderado_ids debe ser una lista de IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        apoderados = User.objects.filter(id__in=apoderado_ids, role__code="APODERADO")
        alumno.apoderados.set(apoderados)
        alumno.save()

        crear_log_actividad(
            request.user,
            f"Asignación de apoderados al alumno ID {alumno.id}.",
            request,
        )
        return Response({"detail": "Apoderados asignados correctamente."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="asignar-alumnos")
    def asignar_alumnos(self, request, pk=None):
        """
        Asigna alumnos a un apoderado.

        Body:
        {
            "alumno_ids": [1, 2, 3]
        }
        """
        apoderado = self.get_object()

        if not (apoderado.role and apoderado.role.code == "APODERADO"):
            return Response(
                {"detail": "Solo puedes asignar alumnos a usuarios con rol APODERADO."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alumno_ids = request.data.get("alumno_ids", [])
        if not isinstance(alumno_ids, list):
            return Response(
                {"detail": "alumno_ids debe ser una lista de IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alumnos = User.objects.filter(id__in=alumno_ids, role__code="ALUMNO")
        apoderado.alumnos.set(alumnos)
        apoderado.save()

        crear_log_actividad(
            request.user,
            f"Asignación de alumnos al apoderado ID {apoderado.id}.",
            request,
        )
        return Response({"detail": "Alumnos asignados correctamente."}, status=status.HTTP_200_OK)

    # --------------------------------------------------------
    #  ACTIVIDAD / LOGS DEL USUARIO
    # --------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="actividad")
    def actividad(self, request, pk=None):
        """
        Devuelve el historial de actividad del usuario.
        Solo ADMIN/DIRECTOR (IsInstitutionalStaff).
        """
        user_obj = self.get_object()
        logs = UserActivityLog.objects.filter(user=user_obj).order_by("-created_at")
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
#  ROLE VIEWSET (CRUD)
# ============================================================

class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD de roles institucionales.
    - ADMIN: crea, edita, elimina
    - Personal institucional: puede listar/ver detalles
    """
    queryset = Role.objects.all().order_by("hierarchy")
    serializer_class = RoleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            perms = [permissions.IsAuthenticated, IsInstitutionalStaff, IsActiveUser]
        else:
            perms = [permissions.IsAuthenticated, IsAdminRole, IsActiveUser]
        return [p() for p in perms]


# ============================================================
#  CUSTOM PERMISSIONS VIEWSET (CRUD)
# ============================================================

class CustomPermissionViewSet(viewsets.ModelViewSet):
    """
    CRUD de permisos personalizados.
    Solo para administradores.
    """
    queryset = CustomPermission.objects.all().order_by("code")
    serializer_class = CustomPermissionSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsAdminRole(), IsActiveUser()]


# ============================================================
#  USER GROUP VIEWSET (CRUD)
# ============================================================

class UserGroupViewSet(viewsets.ModelViewSet):
    """
    CRUD de grupos institucionales (cursos, talleres, niveles, etc.).
    Manejado por personal institucional.
    """
    queryset = UserGroup.objects.all().order_by("name")
    serializer_class = UserGroupSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsInstitutionalStaff(), IsActiveUser()]


# ============================================================
#  NOTIFICATION VIEWSET (CRUD)
# ============================================================

class NotificationViewSet(viewsets.ModelViewSet):
    """
    CRUD de notificaciones internas.

    - Usuarios normales: ven solo sus notificaciones.
    - ADMIN/DIRECTOR: si pasan ?all=1 ven todas.
    - Creación/edición/eliminación: personal institucional.
    """
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Notification.objects.none()

        # ADMIN o DIRECTOR pueden ver todas con ?all=1
        if user.role and user.role.code in ["ADMIN", "DIRECTOR"] and \
                self.request.query_params.get("all") == "1":
            return Notification.objects.all().select_related("user")

        # Por defecto, solo las del usuario
        return Notification.objects.filter(user=user).select_related("user")

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsInstitutionalStaff(), IsActiveUser()]
        return [permissions.IsAuthenticated(), IsActiveUser()]

    def perform_create(self, serializer):
        """
        Si el staff no especifica usuario, se asigna al propio request.user.
        """
        user = serializer.validated_data.get("user") or self.request.user
        serializer.save(user=user)


# ============================================================
#  ACTIVITY LOG VIEWSET
# ============================================================

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de solo lectura para logs de actividad globales.
    Solo ADMIN/DIRECTOR (IsInstitutionalStaff).
    """
    queryset = UserActivityLog.objects.select_related("user").order_by("-created_at")
    serializer_class = ActivityLogSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsInstitutionalStaff(), IsActiveUser()]
