from rest_framework import permissions

# Reutilizamos la lógica de permisos de la app usuarios
from usuarios.permissions import (
    RolePermissionBase,
    IsDocenteRole,
    IsAlumnoRole,
    IsApoderadoRole,
)

from .models import Curso


# ============================================================
#  ALIAS SIMPLES POR ROL (DOCENTE, ALUMNO, APODERADO)
# ============================================================

class IsDocente(IsDocenteRole):
    """
    Permiso para usuarios con rol DOCENTE.
    Alias más corto para usar en la app académica.
    """
    pass


class IsAlumno(IsAlumnoRole):
    """
    Permiso para usuarios con rol ALUMNO.
    """
    pass


class IsApoderado(IsApoderadoRole):
    """
    Permiso para usuarios con rol APODERADO.
    """
    pass


# ============================================================
#  ADMINISTRADOR ACADÉMICO
#  (ADMIN o DIRECTOR)
# ============================================================

class IsAdministradorAcademico(RolePermissionBase):
    """
    Consideramos como 'administradores académicos' a:
    - ADMIN
    - DIRECTOR

    (Puedes ajustar esta lista si en el futuro agregas más roles).
    """
    allowed_roles = ["ADMIN", "DIRECTOR"]


# ============================================================
#  JEFE DE CURSO
# ============================================================

class IsJefeCurso(permissions.BasePermission):
    """
    Permiso para el docente que es Jefe de Curso de un curso dado.

    Lógica:
    - has_permission:
        - Debe estar autenticado
        - Debe ser DOCENTE, ADMIN o DIRECTOR
    - has_object_permission:
        - ADMIN o DIRECTOR siempre pueden.
        - Si el objeto es un Curso -> user == curso.jefe_curso
        - Si el objeto tiene atributo 'curso' -> user == obj.curso.jefe_curso
          (Ej: Asistencia, Evaluación, etc. que referencian a un curso)
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if not getattr(user, "role", None):
            return False

        # Jefe de curso siempre será DOCENTE,
        # pero dejamos que ADMIN y DIRECTOR también pasen esta primera barrera.
        return user.role.code in ["DOCENTE", "ADMIN", "DIRECTOR"]

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated or not getattr(user, "role", None):
            return False

        # ADMIN y DIRECTOR tienen acceso completo
        if user.role.code in ["ADMIN", "DIRECTOR"]:
            return True

        # Si el objeto es directamente un Curso
        if isinstance(obj, Curso):
            return obj.jefe_curso_id == user.id

        # Si el objeto tiene un FK 'curso' (Evaluacion, Asistencia, etc.)
        curso = getattr(obj, "curso", None)
        if isinstance(curso, Curso):
            return curso.jefe_curso_id == user.id

        # Si no sabemos cómo asociarlo a un curso, por seguridad denegamos
        return False


# ============================================================
#  PERMISOS COMBINADOS (OR LÓGICO ENTRE ROLES)
# ============================================================

class IsDocenteOrAdministradorAcademico(permissions.BasePermission):
    """
    Permite acceso si el usuario es:
    - DOCENTE
    - o ADMIN/DIRECTOR (IsAdministradorAcademico)
    """

    def has_permission(self, request, view):
        if IsDocente().has_permission(request, view):
            return True
        if IsAdministradorAcademico().has_permission(request, view):
            return True
        return False


class IsDocenteOrJefeCursoOrAdministradorAcademico(permissions.BasePermission):
    """
    Permite acceso si el usuario es:
    - DOCENTE
    - o JEFE DE CURSO
    - o ADMIN/DIRECTOR
    """

    def has_permission(self, request, view):
        if IsDocente().has_permission(request, view):
            return True
        if IsJefeCurso().has_permission(request, view):
            return True
        if IsAdministradorAcademico().has_permission(request, view):
            return True
        return False
