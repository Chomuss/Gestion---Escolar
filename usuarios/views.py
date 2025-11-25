# usuarios/views.py

from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db import models  # Para Q en filtros

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

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


# ============================================================
#  PERMISOS PERSONALIZADOS POR ROL
# ============================================================

class IsAdminRole(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Administrador."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.code == "ADMIN"
        )


class IsDirectorRole(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Director."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.code == "DIRECTOR"
        )


class IsDocenteRole(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Docente."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.code == "DOCENTE"
        )


class IsAlumnoRole(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Alumno."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.code == "ALUMNO"
        )


class IsApoderadoRole(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Apoderado."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.code == "APODERADO"
        )


class IsAdminOrDirector(permissions.BasePermission):
    """Permite acceso solo a Administradores o Directores."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            and request.user.role.code in ("ADMIN", "DIRECTOR")
        )


# ============================================================
#  AUTENTICACIÓN: LOGIN / LOGOUT
# ============================================================

class LoginView(APIView):
    """
    Inicio de sesión con:
    - Validación de credenciales
    - Bloqueo temporal tras múltiples intentos fallidos
    - Registro de actividad
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        ip = request.META.get("REMOTE_ADDR", None)

        if not username or not password:
            return Response(
                {"detail": "Debe enviar username y password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar bloqueo temporal
        user_obj = None
        try:
            user_obj = User.objects.get(username=username)
            if user_obj.is_temporarily_blocked() or user_obj.is_blocked:
                return Response(
                    {"detail": "Usuario bloqueado temporalmente. Intente más tarde."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except User.DoesNotExist:
            pass

        user = authenticate(request, username=username, password=password)

        if not user:
            # Manejo de intentos fallidos
            if user_obj:
                user_obj.failed_attempts += 1
                if user_obj.failed_attempts >= 5:
                    user_obj.is_blocked = True
                    user_obj.blocked_until = timezone.now() + timedelta(minutes=30)
                user_obj.save()

                UserActivityLog.objects.create(
                    user=user_obj,
                    action="Intento de inicio de sesión fallido",
                    ip_address=ip,
                    user_agent=request.headers.get("User-Agent", ""),
                )

            return Response(
                {"detail": "Credenciales inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Reset de intentos fallidos
        user.failed_attempts = 0
        user.last_login_ip = ip
        user.save()

        # Registrar actividad
        UserActivityLog.objects.create(
            user=user,
            action="Inicio de sesión",
            ip_address=ip,
            user_agent=request.headers.get("User-Agent", ""),
        )

        login(request, user)
        return Response({"detail": "Inicio de sesión exitoso."})


class LogoutView(APIView):
    """
    Cierre de sesión con registro de actividad.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        UserActivityLog.objects.create(
            user=request.user,
            action="Cierre de sesión",
            ip_address=request.META.get("REMOTE_ADDR", None),
            user_agent=request.headers.get("User-Agent", ""),
        )
        logout(request)
        return Response({"detail": "Sesión cerrada correctamente."})


# ============================================================
#  GESTIÓN DE USUARIOS (CRUD + BÚSQUEDA)
# ============================================================

class UserListCreateView(generics.ListCreateAPIView):
    """
    Listado y creación de usuarios.

    - GET: cualquier usuario autenticado puede listar (política básica, luego puedes limitar).
    - POST: solo Administrador / Director pueden crear usuarios.

    Filtros:
    - ?search=
    - ?role=ADMIN/DIRECTOR/DOCENTE/ALUMNO/APODERADO
    - ?active=true/false
    """

    queryset = User.objects.all().select_related("role").prefetch_related(
        "groups_institutional", "extra_permissions"
    )

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdminOrDirector()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.query_params.get("search")
        role_code = self.request.query_params.get("role")
        active = self.request.query_params.get("active")

        if search:
            qs = qs.filter(
                models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
                | models.Q(username__icontains=search)
                | models.Q(email__icontains=search)
            )

        if role_code:
            qs = qs.filter(role__code=role_code)

        if active is not None:
            if active.lower() == "true":
                qs = qs.filter(active=True)
            elif active.lower() == "false":
                qs = qs.filter(active=False)

        return qs

    def perform_create(self, serializer):
        user = serializer.save()
        UserActivityLog.objects.create(
            user=self.request.user,
            action=f"Creó usuario: {user.username}",
            ip_address=self.request.META.get("REMOTE_ADDR", None),
            user_agent=self.request.headers.get("User-Agent", ""),
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Ver, actualizar o eliminar un usuario específico.

    - GET: ver detalle
    - PUT/PATCH: actualizar datos
    - DELETE: eliminar usuario
    """

    queryset = User.objects.all().select_related("role").prefetch_related(
        "groups_institutional", "extra_permissions"
    )

    def get_permissions(self):
        # Solo Admin/Director pueden modificar o eliminar usuarios
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated(), IsAdminOrDirector()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserCreateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        user_updated = serializer.save()
        UserActivityLog.objects.create(
            user=self.request.user,
            action=f"Actualizó usuario: {user_updated.username}",
            ip_address=self.request.META.get("REMOTE_ADDR", None),
            user_agent=self.request.headers.get("User-Agent", ""),
        )

    def perform_destroy(self, instance):
        username = instance.username
        instance.delete()
        UserActivityLog.objects.create(
            user=self.request.user,
            action=f"Eliminó usuario: {username}",
            ip_address=self.request.META.get("REMOTE_ADDR", None),
            user_agent=self.request.headers.get("User-Agent", ""),
        )


# ============================================================
#  PERFIL DEL USUARIO AUTENTICADO
# ============================================================

class MeView(APIView):
    """
    Ver y actualizar el perfil del usuario autenticado.
    - GET: devuelve el perfil del usuario logueado.
    - PATCH: actualizar datos personales (no rol ni permisos).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        # Solo permitir ciertos campos de actualización
        allowed_fields = {
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "gender",
            "birth_date",
            "profile_image",
        }
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = UserCreateSerializer(
            request.user, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        UserActivityLog.objects.create(
            user=request.user,
            action="Actualizó su propio perfil",
            ip_address=request.META.get("REMOTE_ADDR", None),
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response(UserSerializer(request.user).data)


# ============================================================
#  VISTAS ESPECÍFICAS PARA ALUMNO / APODERADO
# ============================================================

class MisAlumnosView(APIView):
    """
    Para APODERADO:
    Lista los alumnos asociados a él.
    """

    permission_classes = [permissions.IsAuthenticated, IsApoderadoRole]

    def get(self, request):
        alumnos = request.user.alumnos.all()
        serializer = UserSerializer(alumnos, many=True)
        return Response(serializer.data)


class MisApoderadosView(APIView):
    """
    Para ALUMNO:
    Lista los apoderados asociados al alumno.
    """

    permission_classes = [permissions.IsAuthenticated, IsAlumnoRole]

    def get(self, request):
        apoderados = request.user.apoderados.all()
        serializer = UserSerializer(apoderados, many=True)
        return Response(serializer.data)


# ============================================================
#  CAMBIO Y REINICIO DE CONTRASEÑA
# ============================================================

class ChangePasswordView(APIView):
    """
    Cambio de contraseña por el propio usuario.
    - Requiere old_password y new_password.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"detail": "Debe enviar old_password y new_password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(old_password):
            return Response(
                {"detail": "La contraseña actual no es correcta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save()

        UserActivityLog.objects.create(
            user=request.user,
            action="Cambió su contraseña",
            ip_address=request.META.get("REMOTE_ADDR", None),
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response({"detail": "Contraseña actualizada correctamente."})


class AdminResetPasswordView(APIView):
    """
    Reinicio de contraseña por parte de Administrador/Director.
    - Recibe user_id y new_password.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrDirector]

    def post(self, request):
        user_id = request.data.get("user_id")
        new_password = request.data.get("new_password")

        if not user_id or not new_password:
            return Response(
                {"detail": "Debe enviar user_id y new_password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.set_password(new_password)
        user.must_change_password = True
        user.save()

        UserActivityLog.objects.create(
            user=request.user,
            action=f"Reinició la contraseña del usuario {user.username}",
            ip_address=request.META.get("REMOTE_ADDR", None),
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response({"detail": "Contraseña reiniciada exitosamente."})


# ============================================================
#  GESTIÓN DE ROLES
# ============================================================

class RoleListCreateView(generics.ListCreateAPIView):
    """
    Listar y crear roles.
    - Solo Administrador puede crear nuevos roles.
    """

    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdminRole()]
        return [permissions.IsAuthenticated()]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Ver, actualizar o eliminar un rol.
    - Solo Administrador.
    """

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


# ============================================================
#  GESTIÓN DE PERMISOS EXTRA
# ============================================================

class CustomPermissionListCreateView(generics.ListCreateAPIView):
    """
    Listar y crear permisos extra.
    - Solo Administrador.
    """

    queryset = CustomPermission.objects.all()
    serializer_class = CustomPermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class CustomPermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Ver, actualizar y eliminar permisos extra.
    - Solo Administrador.
    """

    queryset = CustomPermission.objects.all()
    serializer_class = CustomPermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


# ============================================================
#  GESTIÓN DE GRUPOS INSTITUCIONALES
# ============================================================

class GroupListCreateView(generics.ListCreateAPIView):
    """
    Listar y crear grupos institucionales (cursos, talleres, etc.).
    - Solo Administrador / Director pueden crear grupos.
    """

    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdminOrDirector()]
        return [permissions.IsAuthenticated()]


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Ver, actualizar y eliminar un grupo institucional.
    - Solo Administrador / Director.
    """

    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrDirector]


# ============================================================
#  BLOQUEO / DESBLOQUEO DE USUARIOS
# ============================================================

class BlockUserView(APIView):
    """
    Bloquear temporalmente o permanentemente a un usuario.
    - Solo Administrador / Director.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrDirector]

    def post(self, request):
        user_id = request.data.get("user_id")
        minutes = request.data.get("minutes", None)

        if not user_id:
            return Response(
                {"detail": "Debe enviar user_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_blocked = True
        if minutes:
            try:
                minutes = int(minutes)
                user.blocked_until = timezone.now() + timedelta(minutes=minutes)
            except ValueError:
                return Response(
                    {"detail": "El valor de 'minutes' debe ser numérico."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        user.save()

        UserActivityLog.objects.create(
            user=request.user,
            action=f"Bloqueó al usuario {user.username}",
            ip_address=request.META.get("REMOTE_ADDR", None),
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response({"detail": "Usuario bloqueado correctamente."})


class UnblockUserView(APIView):
    """
    Desbloquear usuario.
    - Solo Administrador / Director.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrDirector]

    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Debe enviar user_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_blocked = False
        user.blocked_until = None
        user.failed_attempts = 0
        user.save()

        UserActivityLog.objects.create(
            user=request.user,
            action=f"Desbloqueó al usuario {user.username}",
            ip_address=request.META.get("REMOTE_ADDR", None),
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response({"detail": "Usuario desbloqueado correctamente."})


# ============================================================
#  NOTIFICACIONES
# ============================================================

class UserNotificationsView(generics.ListAPIView):
    """
    Listar notificaciones del usuario autenticado.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationCreateView(generics.CreateAPIView):
    """
    Crear notificaciones para usuarios.
    - Solo Administrador / Director / Docente.
    """

    serializer_class = NotificationSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def post(self, request, *args, **kwargs):
        # Validar rol emisor
        if not (
            request.user.role
            and request.user.role.code in ("ADMIN", "DIRECTOR", "DOCENTE")
        ):
            return Response(
                {"detail": "No tiene permiso para enviar notificaciones."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().post(request, *args, **kwargs)


class NotificationMarkReadView(APIView):
    """
    Marcar una notificación como leída.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notificación no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.save()
        return Response({"detail": "Notificación marcada como leída."})


# ============================================================
#  AUDITORÍA DE ACTIVIDAD
# ============================================================

class ActivityLogListView(generics.ListAPIView):
    """
    Listar historial de actividad del sistema.
    - Solo Administrador / Director.
    - Filtro opcional: ?user_id=
    """

    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrDirector]

    def get_queryset(self):
        qs = UserActivityLog.objects.all().order_by("-created_at")
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
