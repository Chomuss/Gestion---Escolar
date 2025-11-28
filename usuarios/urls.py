from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    RoleViewSet,
    CustomPermissionViewSet,
    UserGroupViewSet,
    NotificationViewSet,
    ActivityLogViewSet,
)

router = DefaultRouter()

# Usuarios
router.register(r'usuarios', UserViewSet, basename='usuarios')

# Catálogos
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'permisos', CustomPermissionViewSet, basename='permisos')
router.register(r'grupos', UserGroupViewSet, basename='grupos')

# Notificaciones
router.register(r'notificaciones', NotificationViewSet, basename='notificaciones')

# Logs
router.register(r'actividad', ActivityLogViewSet, basename='actividad')

urlpatterns = [
    path('', include(router.urls)),
]
