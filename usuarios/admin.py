from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (
    User,
    Role,
    CustomPermission,
    UserGroup,
    Notification,
    UserActivityLog,
)


# ============================================================
#  ROLES
# ============================================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "hierarchy")
    list_filter = ("code", "hierarchy")
    search_fields = ("code", "description")
    ordering = ("hierarchy",)


# ============================================================
#  PERMISOS PERSONALIZADOS
# ============================================================
@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


# ============================================================
#  GRUPOS INSTITUCIONALES
# ============================================================
@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


# ============================================================
#  USUARIO PERSONALIZADO
# ============================================================
@admin.register(User)
class UserAdmin(DjangoUserAdmin):

    # ------------------------------
    #  Cómo se muestran en la lista
    # ------------------------------
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "active",
        "is_blocked",
        "is_staff",
        "is_superuser",
        "last_login_ip",
        "created_at",
    )

    list_filter = (
        "role",
        "active",
        "is_blocked",
        "is_staff",
        "is_superuser",
        "groups_institutional",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "rut",
    )

    ordering = ("username",)

    # ------------------------------
    #  Read-only fields
    # ------------------------------
    readonly_fields = (
        "last_login",
        "last_login_ip",
        "created_at",
        "updated_at",
        "failed_attempts",
        "blocked_until",
    )

    # ------------------------------
    #  M2M horizontal selectors
    # ------------------------------
    filter_horizontal = (
        "groups_institutional",
        "extra_permissions",
        "apoderados",
    )

    # ------------------------------
    #  Campos agrupados
    # ------------------------------
    fieldsets = (
        ("Cuenta", {
            "fields": (
                "username",
                "password",
                "role",
                "active",
            )
        }),

        ("Información personal", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "rut",
                "phone",
                "address",
                "gender",
                "birth_date",
                "profile_image",
            )
        }),

        ("Relaciones Institucionales", {
            "fields": (
                "groups_institutional",
                "extra_permissions",
                "apoderados",
                "enrollment_year",
            )
        }),

        ("Permisos y Estado del Usuario", {
            "fields": (
                "is_superuser",
                "is_staff",
                "is_blocked",
                "blocked_until",
                "failed_attempts",
                "must_change_password",
            )
        }),

        ("Datos del Sistema", {
            "fields": (
                "last_login",
                "last_login_ip",
            )
        }),

        ("Auditoría", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    # ------------------------------
    #  Configuración para "Añadir usuario"
    # ------------------------------
    add_fieldsets = (
        ("Crear nuevo usuario", {
            "classes": ("wide",),
            "fields": (
                "username",
                "password1",
                "password2",
                "email",
                "role",
                "active",
            ),
        }),
    )


# ============================================================
#  NOTIFICACIONES
# ============================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "level", "is_read", "created_at")
    list_filter = ("level", "is_read")
    search_fields = ("title", "message", "user__username")


# ============================================================
#  LOG DE ACTIVIDAD
# ============================================================
@admin.register(UserActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "ip_address", "created_at")
    search_fields = ("user__username", "action", "ip_address")
    list_filter = ("action", "created_at")
    ordering = ("-created_at",)

    readonly_fields = ("user", "action", "ip_address", "user_agent", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
