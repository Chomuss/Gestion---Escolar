from django.urls import path

from .views import (
    # Auth
    LoginView,
    LogoutView,

    # Usuarios
    UserListCreateView,
    UserDetailView,
    MeView,
    ChangePasswordView,
    AdminResetPasswordView,
    MisAlumnosView,
    MisApoderadosView,

    # Roles
    RoleListCreateView,
    RoleDetailView,

    # Permisos extra
    CustomPermissionListCreateView,
    CustomPermissionDetailView,

    # Grupos
    GroupListCreateView,
    GroupDetailView,

    # Bloqueo/desbloqueo
    BlockUserView,
    UnblockUserView,

    # Notificaciones
    UserNotificationsView,
    NotificationCreateView,
    NotificationMarkReadView,

    # Auditoría
    ActivityLogListView,
)


urlpatterns = [

    # ============================================================
    #  AUTENTICACIÓN
    # ============================================================
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),

    # ============================================================
    #  USUARIOS (CRUD)
    # ============================================================
    path("usuarios/", UserListCreateView.as_view(), name="usuario-list-create"),
    path("usuarios/<int:pk>/", UserDetailView.as_view(), name="usuario-detail"),

    # Perfil del usuario autenticado
    path("usuarios/me/", MeView.as_view(), name="perfil-propio"),
    path("usuarios/me/cambiar-password/", ChangePasswordView.as_view(), name="cambiar-password"),

    # Reset de contraseña por Admin / Director
    path("usuarios/reset-password/", AdminResetPasswordView.as_view(), name="reset-password-admin"),

    # ============================================================
    #  FUNCIONES ESPECÍFICAS ALUMNO / APODERADO
    # ============================================================
    path("usuarios/mis-alumnos/", MisAlumnosView.as_view(), name="mis-alumnos"),
    path("usuarios/mi-apoderado/", MisApoderadosView.as_view(), name="mi-apoderado"),

    # ============================================================
    #  ROLES
    # ============================================================
    path("roles/", RoleListCreateView.as_view(), name="roles-list-create"),
    path("roles/<int:pk>/", RoleDetailView.as_view(), name="roles-detail"),

    # ============================================================
    #  PERMISOS EXTRA
    # ============================================================
    path("permisos/", CustomPermissionListCreateView.as_view(), name="permisos-list-create"),
    path("permisos/<int:pk>/", CustomPermissionDetailView.as_view(), name="permisos-detail"),

    # ============================================================
    #  GRUPOS (cursos, talleres, niveles)
    # ============================================================
    path("grupos/", GroupListCreateView.as_view(), name="grupos-list-create"),
    path("grupos/<int:pk>/", GroupDetailView.as_view(), name="grupos-detail"),

    # ============================================================
    #  BLOQUEO / DESBLOQUEO DE USUARIOS
    # ============================================================
    path("usuarios/bloquear/", BlockUserView.as_view(), name="bloquear-usuario"),
    path("usuarios/desbloquear/", UnblockUserView.as_view(), name="desbloquear-usuario"),

    # ============================================================
    #  NOTIFICACIONES
    # ============================================================
    path("notificaciones/", UserNotificationsView.as_view(), name="notificaciones-usuario"),
    path("notificaciones/crear/", NotificationCreateView.as_view(), name="notificacion-crear"),
    path("notificaciones/<int:pk>/leer/", NotificationMarkReadView.as_view(), name="notificacion-leer"),

    # ============================================================
    #  AUDITORÍA
    # ============================================================
    path("auditoria/", ActivityLogListView.as_view(), name="auditoria"),
]
