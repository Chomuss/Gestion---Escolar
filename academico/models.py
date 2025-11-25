from django.db import models
from django.conf import settings
from django.utils import timezone


# ============================================================
#  UTILIDADES
# ============================================================

User = settings.AUTH_USER_MODEL  # Usa el User de la app usuarios


# ============================================================
#  AÑO Y PERÍODO ACADÉMICO
# ============================================================

class AnioAcademico(models.Model):
    """
    Representa un año académico.
    Permite manejar más de un año en el sistema.
    """
    nombre = models.CharField(max_length=20, unique=True, help_text="Ej: 2025")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Año académico"
        verbose_name_plural = "Años académicos"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return self.nombre


class PeriodoAcademico(models.Model):
    """
    Semestre, trimestre o periodo evaluativo dentro del año académico.
    """
    TIPOS_PERIODO = [
        ("SEM", "Semestre"),
        ("OTRO", "Otro"),
    ]

    anio = models.ForeignKey(AnioAcademico, on_delete=models.CASCADE, related_name="periodos")
    nombre = models.CharField(max_length=50, help_text="Ej: Primer Semestre")
    tipo = models.CharField(max_length=10, choices=TIPOS_PERIODO, default="SEM")
    orden = models.PositiveIntegerField(default=1)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        verbose_name = "Periodo académico"
        verbose_name_plural = "Periodos académicos"
        ordering = ["anio", "orden"]
        unique_together = ("anio", "orden")

    def __str__(self):
        return f"{self.anio} - {self.nombre}"


# ============================================================
#  NIVELES, CURSOS Y SALAS
# ============================================================

class Nivel(models.Model):
    """
    Nivel educativo: Pre-kinder, Kinder, Básica, Media.
    """
    nombre = models.CharField(max_length=50, unique=True, help_text="Ej: Educación Básica")
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """
    Curso/Grupo: 1° Básico A, 2° Medio B, etc.
    """
    anio_academico = models.ForeignKey(AnioAcademico, on_delete=models.CASCADE, related_name="cursos")
    nivel = models.ForeignKey(Nivel, on_delete=models.PROTECT, related_name="cursos")
    nombre = models.CharField(max_length=50, help_text="Ej: 1° Básico A")
    profesor_jefe = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cursos_jefe",
        limit_choices_to={"role__code": "DOCENTE"},
    )

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        unique_together = ("anio_academico", "nombre")
        ordering = ["anio_academico", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.anio_academico})"

    @property
    def total_estudiantes(self):
        return self.matriculas.filter(estado="ACTIVO").count()


class Sala(models.Model):
    """
    Sala de clases.
    """
    nombre = models.CharField(max_length=50, unique=True)
    ubicacion = models.CharField(max_length=100, blank=True)
    capacidad = models.PositiveIntegerField(default=30)

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def __str__(self):
        return self.nombre


# ============================================================
#  ASIGNATURAS Y ASIGNACIÓN DOCENTE
# ============================================================

class Asignatura(models.Model):
    """
    Asignatura o ramo: Matemáticas, Lenguaje, etc.
    """
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    horas_semanales = models.PositiveIntegerField(default=2)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class AsignaturaCursoDocente(models.Model):
    """
    Relación Asignatura - Curso - Docente.
    Permite saber qué docente hace clase de tal asignatura en tal curso.
    """
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="asignaturas_curso")
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name="cursos_asignatura")
    docente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="asignaturas_docente",
        limit_choices_to={"role__code": "DOCENTE"},
    )

    class Meta:
        verbose_name = "Asignación de asignatura"
        verbose_name_plural = "Asignaciones de asignaturas"
        unique_together = ("curso", "asignatura")

    def __str__(self):
        return f"{self.asignatura} - {self.curso} ({self.docente})"


# ============================================================
#  MATRÍCULA / INSCRIPCIÓN
# ============================================================

class Matricula(models.Model):
    """
    Matrícula de un estudiante (User con rol ALUMNO) en un curso para un año académico.
    """
    ESTADOS_MATRICULA = [
        ("ACTIVO", "Activo"),
        ("RETIRADO", "Retirado"),
        ("EGRESADO", "Egresado"),
    ]

    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="matriculas",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="matriculas")
    anio_academico = models.ForeignKey(AnioAcademico, on_delete=models.PROTECT, related_name="matriculas")
    fecha_matricula = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS_MATRICULA, default="ACTIVO")
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        unique_together = ("estudiante", "curso", "anio_academico")

    def __str__(self):
        return f"{self.estudiante} - {self.curso} ({self.anio_academico})"


# ============================================================
#  HORARIO / BLOQUES
# ============================================================

class BloqueHorario(models.Model):
    """
    Bloque horario de una clase específica.
    Define el día, la hora y la sala para un curso y asignatura.
    """
    DIAS_SEMANA = [
        (1, "Lunes"),
        (2, "Martes"),
        (3, "Miércoles"),
        (4, "Jueves"),
        (5, "Viernes"),
    ]

    asignacion = models.ForeignKey(
        AsignaturaCursoDocente,
        on_delete=models.CASCADE,
        related_name="bloques_horario",
    )
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True, related_name="bloques")

    class Meta:
        verbose_name = "Bloque horario"
        verbose_name_plural = "Bloques horarios"
        ordering = ["dia_semana", "hora_inicio"]
        unique_together = ("asignacion", "dia_semana", "hora_inicio")

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin} ({self.asignacion})"


# ============================================================
#  ASISTENCIA
# ============================================================

class Asistencia(models.Model):
    """
    Registro de asistencia de un estudiante a una clase (curso/asignatura) en una fecha específica.
    """
    ESTADOS_ASISTENCIA = [
        ("PRESENTE", "Presente"),
        ("AUSENTE", "Ausente"),
        ("ATRASO", "Atraso"),
        ("JUSTIFICADO", "Ausencia justificada"),
    ]

    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="registros_asistencia",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="asistencias")
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS_ASISTENCIA)
    justificacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="asistencias_registradas",
        limit_choices_to={"role__code__in": ["DOCENTE", "ADMIN", "DIRECTOR"]},
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ("estudiante", "curso", "asignatura", "fecha")
        ordering = ["-fecha", "curso"]

    def __str__(self):
        return f"{self.fecha} - {self.estudiante} - {self.asignatura} ({self.estado})"


# ============================================================
#  EVALUACIONES Y CALIFICACIONES
# ============================================================

class Evaluacion(models.Model):
    """
    Evaluación: prueba, examen, trabajo, tarea, etc.
    Asociada a una asignatura y curso.
    """
    TIPOS_EVALUACION = [
        ("PRUEBA", "Prueba"),
        ("EXAMEN", "Examen"),
        ("TAREA", "Tarea"),
        ("TRABAJO", "Trabajo"),
        ("OTRO", "Otro"),
    ]

    asignacion = models.ForeignKey(
        AsignaturaCursoDocente,
        on_delete=models.CASCADE,
        related_name="evaluaciones",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="evaluaciones",
        null=True,
        blank=True,
    )
    tipo = models.CharField(max_length=20, choices=TIPOS_EVALUACION, default="PRUEBA")
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField(default=timezone.now)
    puntaje_maximo = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    ponderacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Peso de esta evaluación en el promedio del periodo (ej: 20.00 = 20%)",
    )

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="evaluaciones_creadas",
        limit_choices_to={"role__code": "DOCENTE"},
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.titulo} ({self.asignacion})"


class Calificacion(models.Model):
    """
    Calificación de un estudiante en una evaluación específica.
    """
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name="calificaciones")
    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="calificaciones",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    puntaje_obtenido = models.DecimalField(max_digits=6, decimal_places=2)
    observacion = models.CharField(max_length=255, blank=True)
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="calificaciones_registradas",
        limit_choices_to={"role__code": "DOCENTE"},
    )
    registrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        unique_together = ("evaluacion", "estudiante")

    def __str__(self):
        return f"{self.estudiante} - {self.evaluacion} = {self.puntaje_obtenido}"

    @property
    def porcentaje(self):
        if self.evaluacion.puntaje_maximo > 0:
            return (self.puntaje_obtenido / self.evaluacion.puntaje_maximo) * 100
        return 0


class PromedioFinal(models.Model):
    """
    Promedio final de un estudiante en una asignatura/curso/periodo.
    Se puede recalcular a partir de las calificaciones.
    """
    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="promedios_finales",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    asignacion = models.ForeignKey(
        AsignaturaCursoDocente,
        on_delete=models.CASCADE,
        related_name="promedios_finales",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="promedios_finales",
        null=True,
        blank=True,
    )
    promedio = models.DecimalField(max_digits=5, decimal_places=2)
    calculado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promedio final"
        verbose_name_plural = "Promedios finales"
        unique_together = ("estudiante", "asignacion", "periodo")

    def __str__(self):
        return f"{self.estudiante} - {self.asignacion} ({self.periodo}) = {self.promedio}"


# ============================================================
#  OBSERVACIONES ACADÉMICAS Y DISCIPLINARIAS
# ============================================================

class Observacion(models.Model):
    """
    Observaciones respecto al desempeño académico o disciplina del estudiante.
    """
    TIPOS_OBSERVACION = [
        ("ACADEMICA", "Académica"),
        ("DISCIPLINARIA", "Disciplinaria"),
    ]

    NIVELES_GRAVEDAD = [
        ("BAJA", "Baja"),
        ("MEDIA", "Media"),
        ("ALTA", "Alta"),
    ]

    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="observaciones",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observaciones",
    )
    tipo = models.CharField(max_length=20, choices=TIPOS_OBSERVACION)
    gravedad = models.CharField(max_length=10, choices=NIVELES_GRAVEDAD, default="BAJA")
    descripcion = models.TextField()
    fecha = models.DateField(default=timezone.now)
    registrada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="observaciones_registradas",
        limit_choices_to={"role__code__in": ["DOCENTE", "DIRECTOR", "ADMIN"]},
    )
    resuelta = models.BooleanField(default=False)
    resolucion = models.TextField(blank=True)
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Observación"
        verbose_name_plural = "Observaciones"
        ordering = ["-fecha", "estudiante"]

    def __str__(self):
        return f"{self.estudiante} - {self.get_tipo_display()} ({self.gravedad})"

    def marcar_resuelta(self, comentario: str = ""):
        self.resuelta = True
        self.resolucion = comentario
        self.resuelta_en = timezone.now()
        self.save()


# ============================================================
#  SISTEMA DE CORREOS – COLA DE ENVÍO
# ============================================================

class EmailQueue(models.Model):
    """
    Cola de correos para envío asincrónico (Celery / CRON / Thread).
    Se puede usar para cursos completos, apoderados, estudiantes, docentes, etc.
    """

    DESTINATARIO_TIPO = [
        ("USER", "Usuario individual"),
        ("CURSO", "Curso completo"),
        ("APODERADOS", "Apoderados del estudiante"),
    ]

    tipo_destinatario = models.CharField(max_length=20, choices=DESTINATARIO_TIPO)
    destinatario_usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    destinatario_curso = models.ForeignKey(
        "Curso", on_delete=models.SET_NULL, null=True, blank=True
    )

    asunto = models.CharField(max_length=200)
    contenido = models.TextField()

    enviado = models.BooleanField(default=False)
    enviado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Correo en cola"
        verbose_name_plural = "Correos en cola"

    def __str__(self):
        return f"{self.asunto} ({self.get_tipo_destinatario_display()})"


# ============================================================
#  REUNIONES DE APODERADOS
# ============================================================

class ReunionApoderados(models.Model):
    """
    Reuniones programadas por curso o por asignatura.
    """

    curso = models.ForeignKey("Curso", on_delete=models.CASCADE, related_name="reuniones")
    docente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reuniones_docente",
        limit_choices_to={"role__code": "DOCENTE"},
    )
    fecha = models.DateTimeField()
    tema = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reunión de apoderados"
        verbose_name_plural = "Reuniones de apoderados"

    def __str__(self):
        return f"{self.curso} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class AsistenciaReunionApoderado(models.Model):
    """
    Registro de asistencia del apoderado a la reunión.
    """

    reunion = models.ForeignKey(ReunionApoderados, on_delete=models.CASCADE, related_name="asistentes")
    apoderado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reuniones_asistidas",
        limit_choices_to={"role__code": "APODERADO"},
    )
    asistio = models.BooleanField(default=False)
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Asistencia reunión apoderados"
        verbose_name_plural = "Asistencias reuniones apoderados"
        unique_together = ("reunion", "apoderado")

    def __str__(self):
        return f"{self.apoderado} - {self.reunion} ({self.asistio})"


# ============================================================
#  ALERTAS TEMPRANAS (RIESGO ACADÉMICO)
# ============================================================

class AlertaTemprana(models.Model):
    """
    Sistema de seguimiento de riesgo académico.
    Se activa automáticamente cuando:
    - notas bajo cierto umbral
    - muchas ausencias
    - observaciones disciplinarias
    """

    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="alertas",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    curso = models.ForeignKey("Curso", on_delete=models.CASCADE, related_name="alertas")
    motivo = models.CharField(max_length=200)
    descripcion = models.TextField()
    nivel = models.CharField(
        max_length=20,
        choices=[("BAJO", "Bajo"), ("MEDIO", "Medio"), ("ALTO", "Alto")],
        default="BAJO",
    )
    generada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="alertas_generadas",
    )
    fecha = models.DateTimeField(default=timezone.now)
    notificada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Alerta temprana"
        verbose_name_plural = "Alertas tempranas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.estudiante} - {self.nivel} - {self.motivo}"


# ============================================================
#  REPORTE DE NOTAS POR PERIODO
# ============================================================

class ReporteNotasPeriodo(models.Model):
    """
    Reporte consolidado del rendimiento del estudiante por periodo académico.
    Puede generarse automáticamente (cron) o manualmente.
    """

    estudiante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_periodo",
        limit_choices_to={"role__code": "ALUMNO"},
    )
    periodo = models.ForeignKey(
        "PeriodoAcademico",
        on_delete=models.CASCADE,
        related_name="reportes",
    )
    promedio_general = models.DecimalField(max_digits=5, decimal_places=2)
    generado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reporte de notas por periodo"
        verbose_name_plural = "Reportes de notas por periodo"
        unique_together = ("estudiante", "periodo")

    def __str__(self):
        return f"Reporte {self.estudiante} - {self.periodo}"
