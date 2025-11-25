from rest_framework.permissions import BasePermission

class IsAlumno(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == "ALUMNO"


class IsDocente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == "DOCENTE"


class IsApoderado(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == "APODERADO"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == "ADMIN"


class IsDirector(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.code == "DIRECTOR"
