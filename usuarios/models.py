from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError


# ============================================================
#  UTILIDAD: VALIDACIÓN DE RUT CHILENO
# ============================================================

def validar_rut(rut: str) -> bool:
    """
    - Elimina puntos y guiones.
    - Acepta K/k como dígito verificador.
    - Retorna True si el RUT es válido, False en caso contrario.
    """
    if not rut:
        return False

    rut = rut.replace(".", "").replace("-", "").upper().strip()

    # Debe tener al menos 2 caracteres: cuerpo + dígito verificador
    if len(rut) < 2:
        return False

    cuerpo = rut[:-1]
    dv = rut[-1]

    if not cuerpo.isdigit():
        return False

    suma = 0
    multiplicador = 2

    for d in reversed(cuerpo):
        suma += int(d) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = suma % 11
    dv_calc = 11 - resto

    if dv_calc == 11:
        dv_calc = "0"
    elif dv_calc == 10:
        dv_calc = "K"
    else:
        dv_calc = str(dv_calc)

    return dv == dv_calc


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

    code = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        unique=True,
        help_text="Código del rol institucional (ADMIN, DIRECTOR, DOCENTE, ALUMNO, APODERADO)."
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción general del rol y sus responsabilidades."
    )

    # Jerarquía: 1 = máximo acceso / 5 = acceso básico
    hierarchy = models.PositiveIntegerField(
        default=5,
        help_text="Nivel jerárquico del rol (1 = más alto, 5 = más bajo)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["hierarchy", "code"]
        indexes = [
            models.Index(fields=["code"], name="idx_role_code"),
        ]

    def __str__(self):
        return self.get_code_display()


# ============================================================
#  PERMISOS TRANSVERSALES
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
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Código interno del permiso. Ej: 'ver_asistencia'."
    )
    name = models.CharField(
        max_length=150,
        help_text="Nombre legible del permiso."
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del alcance del permiso."
    )

    class Meta:
        verbose_name = "Permiso personalizado"
        verbose_name_plural = "Permisos personalizados"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"], name="idx_perm_code"),
        ]

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
    name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Nombre del grupo institucional. Ej: '7°A', 'Docentes Matemática'."
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción general del grupo."
    )

    class Meta:
        verbose_name = "Grupo institucional"
        verbose_name_plural = "Grupos institucionales"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ============================================================
#  USUARIO INSTITUCIONAL
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
    rut = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        help_text="RUT del usuario (sin puntos, con guion). Obligatorio para ALUMNO y APODERADO."
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Rol institucional asignado al usuario."
    )

    # Información personal
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Teléfono principal del usuario."
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        help_text="Dirección del usuario."
    )
    gender = models.CharField(
        max_length=20,
        blank=True,
        help_text="Género declarado (opcional)."
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de nacimiento del usuario."
    )

    # Relación Apoderado → Alumno(s)
    apoderados = models.ManyToManyField(
        'self',
        related_name='alumnos',
        symmetrical=False,
        blank=True,
        help_text="Relación entre alumnos y sus apoderados."
    )

    # Permisos adicionales
    extra_permissions = models.ManyToManyField(
        CustomPermission,
        blank=True,
        help_text="Permisos adicionales específicos para este usuario."
    )

    # Grupos institucionales
    groups_institutional = models.ManyToManyField(
        UserGroup,
        blank=True,
        help_text="Grupos institucionales a los que pertenece el usuario."
    )

    # Seguridad avanzada
    failed_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad de intentos fallidos de inicio de sesión."
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text="Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión."
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Última dirección IP registrada en el inicio de sesión."
    )
    is_blocked = models.BooleanField(
        default=False,
        help_text="Indica si el usuario está bloqueado manualmente."
    )
    blocked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora hasta la cual el usuario se encuentra bloqueado temporalmente."
    )

    # Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del usuario."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última fecha de actualización del usuario."
    )

    # Datos administrativos
    enrollment_year = models.CharField(
        max_length=10,
        blank=True,
        help_text="Año de ingreso/matrícula del usuario (aplica a alumnos)."
    )
    active = models.BooleanField(
        default=True,
        help_text="Indica si el usuario está activo en el sistema institucional."
    )

    # Foto institucional
    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True,
        help_text="Fotografía de perfil institucional."
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]
        indexes = [
            models.Index(fields=["rut"], name="idx_user_rut"),
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["role"], name="idx_user_role"),
        ]

    # ---------------------------
    # VALIDACIÓN Y NORMALIZACIÓN
    # ---------------------------

    def clean(self):
        super().clean()

        errors = {}

        # Normalizar email
        if self.email:
            self.email = self.email.strip().lower()

        # Normalizar y validar RUT según rol
        if self.rut:
            rut_normalizado = self.rut.replace(".", "").replace("-", "").upper().strip()
            self.rut = rut_normalizado

            if not validar_rut(self.rut):
                errors["rut"] = "El RUT ingresado no es válido."
        else:
            # Si no hay RUT y el rol exige RUT
            if self.role and self.role.code in ("ALUMNO", "APODERADO"):
                errors["rut"] = "El RUT es obligatorio para alumnos y apoderados."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ---------------------------
    # MÉTODOS DE UTILIDAD
    # ---------------------------

    def is_temporarily_blocked(self):
        """
        True si el usuario está bloqueado temporalmente
        por fecha (blocked_until en el futuro).
        """
        return bool(self.blocked_until and timezone.now() < self.blocked_until)

    @property
    def is_effectively_active(self):
        """
        Indica si el usuario está efectivamente activo:
        - active = True
        - is_blocked = False
        - no está temporalmente bloqueado
        """
        if not self.active:
            return False
        if self.is_blocked:
            return False
        if self.is_temporarily_blocked():
            return False
        return True

    @property
    def full_name(self):
        """
        Devuelve el nombre completo ya formateado.
        """
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    @property
    def role_code(self):
        """
        Devuelve el código del rol (ADMIN, DOCENTE, etc.) o None.
        """
        return self.role.code if self.role else None

    @property
    def is_student(self):
        return self.role_code == "ALUMNO"

    @property
    def is_guardian(self):
        return self.role_code == "APODERADO"

    @property
    def is_teacher(self):
        return self.role_code == "DOCENTE"

    @property
    def is_admin_institutional(self):
        return self.role_code in ("ADMIN", "DIRECTOR")

    def __str__(self):
        return f"{self.username} ({self.role.get_code_display() if self.role else 'Sin rol'})"


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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="Usuario asociado a la acción registrada."
    )
    action = models.CharField(
        max_length=255,
        help_text="Descripción breve de la acción realizada."
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Dirección IP desde donde se realizó la acción."
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User-Agent del navegador o cliente que realizó la acción."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se registró la acción."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Registro de actividad de usuario"
        verbose_name_plural = "Registros de actividad de usuario"

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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Usuario destinatario de la notificación."
    )
    title = models.CharField(
        max_length=200,
        help_text="Título breve de la notificación."
    )
    message = models.TextField(
        help_text="Contenido de la notificación."
    )
    level = models.CharField(
        max_length=20,
        choices=[
            ('INFO', 'Información'),
            ('WARN', 'Advertencia'),
            ('URGENT', 'Urgente'),
        ],
        default='INFO',
        help_text="Nivel de prioridad de la notificación."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Indica si el usuario ya ha leído la notificación."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación de la notificación."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"{self.title} - {self.user.username}"
