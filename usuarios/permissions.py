from rest_framework import permissions


# ============================================================
#  CLASE BASE PARA PERMISOS POR ROL
# ============================================================

class RolePermissionBase(permissions.BasePermission):
    """
    Clase base que permite validar el rol del usuario sin duplicar código.
    Todas las clases hijas solo necesitan definir:
    - allowed_roles = ['ADMIN', 'DOCENTE'] por ejemplo
    """
    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user

        # No autenticado
        if not user or not user.is_authenticated:
            return False

        # Sin rol asociado
        if not user.role:
            return False

        # Validar si el rol está dentro de los permitidos
        return user.role.code in self.allowed_roles



# ============================================================
#  PERMISOS SEGÚN ROLES INSTITUCIONALES
# ============================================================

class IsAdminRole(RolePermissionBase):
    """Permiso exclusivo de administradores."""
    allowed_roles = ['ADMIN']


class IsDirectorRole(RolePermissionBase):
    """Permiso exclusivo del director."""
    allowed_roles = ['DIRECTOR']


class IsDocenteRole(RolePermissionBase):
    """Permiso exclusivo para docentes."""
    allowed_roles = ['DOCENTE']


class IsAlumnoRole(RolePermissionBase):
    """Permiso exclusivo para estudiantes."""
    allowed_roles = ['ALUMNO']


class IsApoderadoRole(RolePermissionBase):
    """Permiso exclusivo para apoderados."""
    allowed_roles = ['APODERADO']




# ============================================================
#  PERMISOS POR JERARQUÍA
# ============================================================

class HasHigherHierarchy(permissions.BasePermission):
    """
    Permite el acceso solamente a usuarios que tengan menor 'hierarchy'
    en su rol.
    
    Ejemplo:
    - ADMIN (1) puede ver/modificar cualquier usuario
    - DIRECTOR (2) puede ver/modificar DOCENTE/ALUMNO/APODERADO
    """

    def has_object_permission(self, request, view, obj):
        current_user = request.user

        if not current_user.is_authenticated:
            return False

        # Si el objeto no tiene rol
        if not obj.role or not current_user.role:
            return False

        # Jerarquía más baja = número mayor (1 es el más alto)
        return current_user.role.hierarchy <= obj.role.hierarchy




# ============================================================
#  PERMISO PARA PERSONAL INSTITUCIONAL
#  (Administrador, Director, Docente)
# ============================================================

class IsInstitutionalStaff(RolePermissionBase):
    """
    Permiso general para personal institucional:
    - ADMIN
    - DIRECTOR
    - DOCENTE
    """
    allowed_roles = ['ADMIN', 'DIRECTOR', 'DOCENTE']




# ============================================================
#  PERMISO PARA ACCESO DE APODERADO AL ALUMNO
# ============================================================

class CanAccessStudent(permissions.BasePermission):
    """
    Permite que un apoderado acceda solo a información de su alumno.
    También permite acceso para administradores y directores.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Permitir acceso a admins y directores
        if user.role and user.role.code in ['ADMIN', 'DIRECTOR']:
            return True

        # Si el usuario es un apoderado
        if user.role and user.role.code == "APODERADO":
            return obj in user.alumnos.all()

        return False




# ============================================================
#  PERMISOS BASADOS EN CUSTOM PERMISSIONS
# ============================================================

class HasCustomPermission(permissions.BasePermission):
    """
    Verifica si el usuario tiene un permiso personalizado específico.
    Usado con:
        required_permission = 'ver_asistencia'
    """

    required_permission = None

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if not self.required_permission:
            return False

        # Revisar si el usuario tiene el permiso custom
        return user.extra_permissions.filter(code=self.required_permission).exists()



# ============================================================
#  PERMISO: SOLO PROPIETARIO O ADMINISTRADOR
# ============================================================

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permite acceso a:
    - El dueño del objeto (por ejemplo /api/users/<id>/)
    - Un administrador
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        # Administrador siempre puede
        if user.role and user.role.code == "ADMIN":
            return True

        # El usuario solo puede ver/modificar su propio registro
        return obj.id == user.id



# ============================================================
#  PERMISO GENERAL PARA ACCESO SOLO A USUARIOS ACTIVOS
# ============================================================

class IsActiveUser(permissions.BasePermission):
    """
    Asegura que el usuario esté activo (no desactivado, no bloqueado).
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        return user.is_effectively_active