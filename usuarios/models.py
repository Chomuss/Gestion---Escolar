from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# ============================================================
#  ROLES INSTITUCIONALES (FIJOS SEGÚN TU DOCUMENTO)
# ============================================================

class Role(models.Model):
    """
    Roles institucionales definidos para el sistema escolar:
    - Administrador
    - Director
    - Docente
    - Alumno
    - Apoderado
    """

    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('DIRECTOR', 'Director'),
        ('DOCENTE', 'Docente'),
        ('ALUMNO', 'Alumno'),
        ('APODERADO', 'Apoderado'),
    ]

    code = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    # Jerarquía: 1 = máximo acceso / 5 = acceso básico
    hierarchy = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.get_code_display()
    

# ============================================================
#  PERMISOS TRANSVERSALES (EXTRA)
# ============================================================

class CustomPermission(models.Model):
    """
    Permisos extra, específicos de la institución:
    - ver_asistencia
    - modificar_asistencia
    - registrar_notas
    - ver_notas
    - gestionar_comunicados
    - etc.
    """
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ============================================================
#  GRUPOS INSTITUCIONALES
# ============================================================

class UserGroup(models.Model):
    """
    Grupos institucionales:
    - Cursos (7°A, 2°B, 1° Medio C)
    - Niveles (Básica, Media)
    - Talleres (Fútbol, Música)
    - Equipos (Docentes de Matemática)
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ============================================================
#  PERFIL COMPLETO DE USUARIO
# ============================================================
class User(AbstractUser):
    """
    Usuario institucional con ampliación de perfil, trazabilidad
    y cumplimiento de requisitos de un sistema escolar.
    """

    # Redefinir campos para evitar conflictos con auth.User
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="usuarios_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="usuarios_user_permissions",
        blank=True
    )

    # Información institucional
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    # Información personal
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # Relación Apoderado → Alumno(s)
    apoderados = models.ManyToManyField(
        'self',
        related_name='alumnos',
        symmetrical=False,
        blank=True
    )

    # Permisos adicionales
    extra_permissions = models.ManyToManyField(CustomPermission, blank=True)

    # Grupos institucionales
    groups_institutional = models.ManyToManyField(UserGroup, blank=True)

    # Seguridad avanzada
    failed_attempts = models.PositiveIntegerField(default=0)
    must_change_password = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Datos administrativos
    enrollment_year = models.CharField(max_length=10, blank=True)
    active = models.BooleanField(default=True)

    # Foto institucional
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def is_temporarily_blocked(self):
        """True si el usuario está bloqueado temporalmente."""
        return self.blocked_until and timezone.now() < self.blocked_until

    def __str__(self):
        return f"{self.username} ({self.role})"


# ============================================================
#  LOG DE ACTIVIDAD
# ============================================================

class UserActivityLog(models.Model):
    """
    Registra:
    - Inicios de sesión
    - Cambios en datos sensibles
    - Acciones administrativas
    - Intentos de acceso
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.action}"


# ============================================================
#  NOTIFICACIONES
# ============================================================

class Notification(models.Model):
    """
    Notificaciones internas:
    - Cambios de horario
    - Evaluaciones nuevas
    - Comunicados
    - Advertencias
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    level = models.CharField(
        max_length=20,
        choices=[('INFO', 'Información'), ('WARN', 'Advertencia'), ('URGENT', 'Urgente')],
        default='INFO'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
