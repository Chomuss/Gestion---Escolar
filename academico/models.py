from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


# ============================================================
#  CONSTANTES COMUNES
# ============================================================

USER_MODEL = settings.AUTH_USER_MODEL


# ============================================================
#  PERÍODOS ACADÉMICOS
# ============================================================


class PeriodoAcademico(models.Model):
    """
    Representa un período académico (anual, semestral, trimestral, etc.).
    Permite manejar horarios, evaluaciones y reportes por periodo.
    """

    TIPO_CHOICES = [
        ("ANUAL", "Anual"),
        ("SEMESTRAL", "Semestral"),
        ("TRIMESTRAL", "Trimestral"),
        ("BIMESTRAL", "Bimestral"),
    ]

    nombre = models.CharField(
        max_length=100,
        help_text="Nombre interno del período (Ej: 2025 - Semestre 1)."
    )
    anio = models.PositiveIntegerField(
        help_text="Año académico (Ej: 2025)."
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="ANUAL"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(
        default=True,
        help_text="Indica si es el período activo actual."
    )

    class Meta:
        verbose_name = "Período académico"
        verbose_name_plural = "Períodos académicos"
        ordering = ["-anio", "tipo"]

    def __str__(self):
        return f"{self.nombre} ({self.anio} - {self.tipo})"

    def clean(self):
        super().clean()
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha de término debe ser posterior a la fecha de inicio.")


# ============================================================
#  CURSOS
# ============================================================


class Curso(models.Model):
    """
    Representa un curso/sección del establecimiento.
    Ejemplos: 7° Básico A, 2° Medio B, etc.
    """

    nombre = models.CharField(
        max_length=50,
        help_text="Nombre del curso (Ej: 7°A, 2°B)."
    )
    nivel = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nivel educativo (Ej: 7° Básico, 2° Medio)."
    )
    capacidad_maxima = models.PositiveIntegerField(
        default=45,
        help_text="Capacidad máxima de estudiantes."
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="cursos",
        help_text="Período académico al que pertenece el curso.",
    )
    jefe_curso = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cursos_jefe",
        help_text="Docente jefe de curso.",
    )
    estudiantes = models.ManyToManyField(
        USER_MODEL,
        blank=True,
        related_name="cursos_estudiante",
        help_text="Estudiantes matriculados en este curso.",
    )

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        unique_together = ("nombre", "periodo")
        ordering = ["periodo", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.periodo.anio})"

    def clean(self):
        super().clean()
        if self.capacidad_maxima <= 0:
            raise ValidationError("La capacidad máxima debe ser mayor a cero.")


# ============================================================
#  ASIGNATURAS
# ============================================================


class Asignatura(models.Model):
    """
    Asignatura impartida en la institución.
    """

    TIPO_CHOICES = [
        ("NORMAL", "Asignatura regular"),
        ("TALLER", "Taller"),
        ("REFUERZO", "Refuerzo"),
        ("LIBRE", "Libre disposición"),
    ]

    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="NORMAL"
    )
    carga_horaria_semanal = models.PositiveIntegerField(
        default=2,
        help_text="Horas pedagógicas semanales asignadas."
    )

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# ============================================================
#  SALAS Y RECURSOS
# ============================================================


class Sala(models.Model):
    """
    Sala o dependencia física donde se realizan clases o actividades.
    """

    TIPO_CHOICES = [
        ("SALA_CLASE", "Sala de clases"),
        ("LABORATORIO", "Laboratorio"),
        ("BIBLIOTECA", "Biblioteca"),
        ("TALLER", "Taller"),
        ("OTRO", "Otro"),
    ]

    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="SALA_CLASE"
    )
    capacidad = models.PositiveIntegerField(default=40)
    ubicacion = models.CharField(max_length=200, blank=True)
    recursos_basicos = models.TextField(
        blank=True,
        help_text="Descripción breve de recursos disponibles (proyector, audio, computadores, etc.).",
    )

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Recurso(models.Model):
    """
    Recurso adicional que puede estar asociado a una sala.
    Ejemplos: Notebook, Data, Equipo de sonido, etc.
    """

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    sala = models.ForeignKey(
        Sala,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recursos",
        help_text="Sala donde se encuentra el recurso (opcional).",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ============================================================
#  BLOQUES HORARIOS Y HORARIOS DE CLASE
# ============================================================


class BloqueHorario(models.Model):
    """
    Define un bloque horario genérico (día + hora inicio/fin).
    Luego puede asignarse a cursos, asignaturas, salas, etc.
    """

    DIA_CHOICES = [
        (1, "Lunes"),
        (2, "Martes"),
        (3, "Miércoles"),
        (4, "Jueves"),
        (5, "Viernes"),
    ]

    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="bloques_horarios",
    )
    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        verbose_name = "Bloque horario"
        verbose_name_plural = "Bloques horarios"
        ordering = ["periodo", "dia_semana", "hora_inicio"]
        unique_together = ("periodo", "dia_semana", "hora_inicio", "hora_fin")

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio} - {self.hora_fin} ({self.periodo})"

    def clean(self):
        super().clean()
        if self.hora_fin <= self.hora_inicio:
            raise ValidationError("La hora de término debe ser posterior a la hora de inicio.")


class HorarioCurso(models.Model):
    """
    Representa una clase específica en un bloque horario:
    Curso + Asignatura + Docente + Sala + Bloque.
    También soporta cambios por periodo (rotación semestral).
    """

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.PROTECT,
        related_name="horarios",
    )
    docente = models.ForeignKey(
        USER_MODEL,
        on_delete=models.PROTECT,
        related_name="horarios_docente",
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.PROTECT,
        related_name="horarios_sala",
    )
    bloque = models.ForeignKey(
        BloqueHorario,
        on_delete=models.PROTECT,
        related_name="horarios_bloque",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="horarios",
    )
    es_rotativo = models.BooleanField(
        default=False,
        help_text="Indica si este horario corresponde a una rotación especial dentro del período.",
    )

    class Meta:
        verbose_name = "Horario de curso"
        verbose_name_plural = "Horarios de curso"
        ordering = ["curso", "bloque"]
        unique_together = ("curso", "asignatura", "docente", "sala", "bloque", "periodo")

    def __str__(self):
        return f"{self.curso} - {self.asignatura} - {self.bloque}"


# ============================================================
#  ASISTENCIA
# ============================================================


class Asistencia(models.Model):
    """
    Registro de asistencia por estudiante, curso y fecha.
    """

    ESTADO_CHOICES = [
        ("PRESENTE", "Presente"),
        ("AUSENTE", "Ausente"),
        ("ATRASO", "Atraso"),
        ("JUSTIFICADO", "Ausencia justificada"),
    ]

    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asistencias",
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="asistencias",
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asistencias",
        help_text="Opcional: asistencia por asignatura.",
    )
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    motivo_inasistencia = models.TextField(
        blank=True,
        help_text="Motivo si el estudiante estuvo ausente o con atraso.",
    )
    es_justificada = models.BooleanField(default=False)
    registrado_por = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asistencias_registradas",
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ["-fecha"]
        unique_together = ("estudiante", "curso", "fecha", "asignatura")

    def __str__(self):
        return f"{self.estudiante} - {self.curso} - {self.fecha} ({self.estado})"


# ============================================================
#  EVALUACIONES Y CALIFICACIONES
# ============================================================


class Evaluacion(models.Model):
    """
    Evaluación asociada a un curso y asignatura.
    """

    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("ATRASADA", "Atrasada"),
        ("PUBLICADA", "Publicada"),
    ]

    TIPO_CHOICES = [
        ("PRUEBA", "Prueba"),
        ("TAREA", "Tarea"),
        ("PROYECTO", "Proyecto"),
        ("EXAMEN", "Examen"),
        ("OTRO", "Otro"),
    ]

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="evaluaciones",
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.PROTECT,
        related_name="evaluaciones",
    )
    docente = models.ForeignKey(
        USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evaluaciones_docente",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="evaluaciones",
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="PRUEBA"
    )
    fecha_evaluacion = models.DateField()
    fecha_limite_publicacion = models.DateField(
        help_text="Fecha límite institucional para publicar las notas."
    )
    fecha_publicacion = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="PENDIENTE",
    )
    ponderacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Ponderación de la evaluación dentro del promedio (0 a 100).",
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ["-fecha_evaluacion"]

    def __str__(self):
        return f"{self.titulo} - {self.curso} - {self.asignatura}"

    def clean(self):
        super().clean()
        if self.fecha_limite_publicacion < self.fecha_evaluacion:
            raise ValidationError("La fecha límite de publicación no puede ser anterior a la fecha de evaluación.")


class Calificacion(models.Model):
    """
    Nota obtenida por un estudiante en una evaluación.
    """

    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name="calificaciones",
    )
    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calificaciones",
    )
    nota = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(7.0)],
        help_text="Nota en escala 1.0 a 7.0.",
    )
    observaciones = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    origen = models.CharField(
        max_length=20,
        default="MANUAL",
        help_text="Origen del registro (MANUAL, EXCEL, IMPORTADO).",
    )

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        unique_together = ("evaluacion", "estudiante")
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.estudiante} - {self.evaluacion} ({self.nota})"


class PromedioFinal(models.Model):
    """
    Promedio final de un estudiante en una asignatura y período.
    """

    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="promedios_finales",
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="promedios_finales",
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name="promedios_finales",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="promedios_finales",
    )
    promedio = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(7.0)],
    )
    aprobado = models.BooleanField(default=False)
    fecha_calculo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promedio final"
        verbose_name_plural = "Promedios finales"
        unique_together = ("estudiante", "curso", "asignatura", "periodo")

    def __str__(self):
        return f"{self.estudiante} - {self.asignatura} ({self.promedio})"


# ============================================================
#  OBSERVACIONES, ALERTAS E INTERVENCIONES
# ============================================================


class Observacion(models.Model):
    """
    Observaciones académicas o de convivencia de un estudiante.
    """

    TIPO_CHOICES = [
        ("ACADEMICA", "Académica"),
        ("CONVIVENCIA", "Convivencia escolar"),
        ("TARDANZA", "Atrasos"),
        ("OTRO", "Otro"),
    ]

    GRAVEDAD_CHOICES = [
        ("BAJA", "Baja"),
        ("MEDIA", "Media"),
        ("ALTA", "Alta"),
    ]

    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="observaciones",
    )
    autor = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observaciones_registradas",
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observaciones",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="OTRO"
    )
    gravedad = models.CharField(
        max_length=20,
        choices=GRAVEDAD_CHOICES,
        default="BAJA"
    )
    descripcion = models.TextField()
    requiere_seguimiento = models.BooleanField(default=False)
    fecha = models.DateField(default=timezone.now)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Observación"
        verbose_name_plural = "Observaciones"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.estudiante} - {self.tipo} - {self.gravedad}"


class AlertaTemprana(models.Model):
    """
    Alerta temprana asociada a un estudiante por riesgo académico o de convivencia.
    Generada automáticamente o manualmente.
    """

    ORIGEN_CHOICES = [
        ("ASISTENCIA", "Asistencia"),
        ("NOTAS", "Notas"),
        ("DISCIPLINA", "Disciplina"),
        ("MIXTO", "Mixto"),
    ]

    ESTADO_CHOICES = [
        ("ABIERTA", "Abierta"),
        ("EN_SEGUIMIENTO", "En seguimiento"),
        ("CERRADA", "Cerrada"),
    ]

    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alertas_tempranas",
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_tempranas",
    )
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    descripcion = models.TextField()
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=[("BAJO", "Bajo"), ("MEDIO", "Medio"), ("ALTO", "Alto")],
        default="MEDIO",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="ABIERTA"
    )
    creada_por = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Alerta temprana"
        verbose_name_plural = "Alertas tempranas"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Alerta {self.origen} - {self.estudiante} ({self.nivel_riesgo})"


class Intervencion(models.Model):
    """
    Intervención realizada para abordar una observación o alerta temprana.
    """

    ESTADO_CHOICES = [
        ("ABIERTA", "Abierta"),
        ("EN_PROCESO", "En proceso"),
        ("CERRADA", "Cerrada"),
    ]

    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="intervenciones",
    )
    alerta = models.ForeignKey(
        AlertaTemprana,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intervenciones",
    )
    observacion = models.ForeignKey(
        Observacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intervenciones",
    )
    responsable = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intervenciones_responsable",
    )
    descripcion = models.TextField()
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="ABIERTA"
    )
    resultado = models.TextField(blank=True)

    class Meta:
        verbose_name = "Intervención"
        verbose_name_plural = "Intervenciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.estudiante} - {self.estado}"


# ============================================================
#  REUNIONES CON APODERADOS
# ============================================================


class ReunionApoderados(models.Model):
    """
    Reunión entre el establecimiento y apoderados,
    ya sea individual (por alumno) o grupal (por curso).
    """

    TIPO_CHOICES = [
        ("INDIVIDUAL", "Individual (por alumno)"),
        ("GRUPAL", "Grupal (por curso)"),
    ]

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="INDIVIDUAL"
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reuniones",
    )
    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reuniones_estudiante",
        help_text="Aplicable en reuniones individuales.",
    )
    apoderado = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reuniones_apoderado",
    )
    docente = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reuniones_docente",
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField(null=True, blank=True)
    temas_tratados = models.TextField()
    acuerdos = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reunión con apoderados"
        verbose_name_plural = "Reuniones con apoderados"
        ordering = ["-fecha", "-hora_inicio"]

    def __str__(self):
        base = f"Reunión {self.get_tipo_display()} - {self.fecha}"
        if self.curso:
            base += f" - {self.curso}"
        if self.estudiante:
            base += f" - {self.estudiante}"
        return base

class MinutaReunion(models.Model):
    """
    Minuta asociada a una reunión de apoderados.
    Permite registrar el detalle formal de lo conversado y los acuerdos.
    """

    reunion = models.ForeignKey(
        ReunionApoderados,
        on_delete=models.CASCADE,
        related_name="minutas",
        help_text="Reunión a la que pertenece esta minuta.",
    )
    autor = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="minutas_reunion_autor",
        help_text="Usuario que redactó la minuta.",
    )
    titulo = models.CharField(
        max_length=200,
        help_text="Título o encabezado de la minuta."
    )
    resumen_general = models.TextField(
        help_text="Resumen general de los temas tratados en la reunión."
    )
    acuerdos_detallados = models.TextField(
        blank=True,
        help_text="Detalle de acuerdos, compromisos y responsables."
    )
    compromisos_apoderados = models.TextField(
        blank=True,
        help_text="Compromisos asumidos por apoderados."
    )
    compromisos_establecimiento = models.TextField(
        blank=True,
        help_text="Compromisos asumidos por el establecimiento (docentes, UTP, dirección, etc.)."
    )
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones adicionales o comentarios relevantes."
    )
    archivo_pdf = models.FileField(
        upload_to="reuniones/minutas/pdf/",
        null=True,
        blank=True,
        help_text="Versión en PDF de la minuta (opcional)."
    )
    creada_en = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación de la minuta."
    )
    actualizada_en = models.DateTimeField(
        auto_now=True,
        help_text="Última fecha de actualización de la minuta."
    )

    class Meta:
        verbose_name = "Minuta de reunión"
        verbose_name_plural = "Minutas de reuniones"
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Minuta - {self.titulo} ({self.reunion})"


class AsistenciaReunionApoderado(models.Model):
    """
    Registro de asistencia de apoderados a una reunión.
    Permite también marcar temas específicos tratados por alumno.
    """

    reunion = models.ForeignKey(
        ReunionApoderados,
        on_delete=models.CASCADE,
        related_name="asistencias_apoderados",
    )
    apoderado = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asistencias_reuniones",
    )
    estudiante = models.ForeignKey(
        USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asistencias_reuniones_estudiante",
    )
    asistio = models.BooleanField(default=False)
    justificacion = models.TextField(blank=True)
    temas_tratados = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia a reunión de apoderado"
        verbose_name_plural = "Asistencias a reuniones de apoderados"
        unique_together = ("reunion", "apoderado", "estudiante")

    def __str__(self):
        return f"{self.reunion} - {self.apoderado} - {'Asistió' if self.asistio else 'No asistió'}"


# ============================================================
#  REPORTES DE NOTAS POR PERÍODO
# ============================================================


class ReporteNotasPeriodo(models.Model):
    """
    Representa un reporte consolidado de notas por curso/asignatura/período.
    Puede generar archivos PDF/Excel asociados.
    """

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="reportes_notas",
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_notas",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="reportes_notas",
    )
    generado_por = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_notas_generados",
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    archivo_pdf = models.FileField(
        upload_to="reportes/notas/pdf/",
        null=True,
        blank=True,
    )
    archivo_excel = models.FileField(
        upload_to="reportes/notas/excel/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Reporte de notas por período"
        verbose_name_plural = "Reportes de notas por período"
        ordering = ["-fecha_generacion"]

    def __str__(self):
        return f"Reporte {self.curso} - {self.asignatura or 'Todas'} - {self.periodo}"


# ============================================================
#  ARCHIVOS ADJUNTOS GENÉRICOS
# ============================================================


class ArchivoAdjunto(models.Model):
    """
    Archivo adjunto genérico, vinculado mediante GenericForeignKey.
    Se puede adjuntar a observaciones, intervenciones, reuniones, etc.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    contenido_objeto = GenericForeignKey("content_type", "object_id")

    archivo = models.FileField(upload_to="adjuntos/")
    descripcion = models.CharField(max_length=255, blank=True)
    subido_por = models.ForeignKey(
        USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archivos_adjuntos_subidos",
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo adjunto"
        verbose_name_plural = "Archivos adjuntos"
        ordering = ["-fecha_subida"]

    def __str__(self):
        return self.descripcion or f"Adjunto #{self.id}"


# ============================================================
#  COLA DE CORREOS (EMAIL QUEUE)
# ============================================================


class EmailQueue(models.Model):
    """
    Cola de correos a enviar (SendGrid u otro proveedor).
    Útil para notificaciones académicas (alertas, reuniones, reportes).
    """

    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("ENVIADO", "Enviado"),
        ("FALLIDO", "Fallido"),
    ]

    destinatario = models.EmailField()
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    enviar_despues_de = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha/hora a partir de la cual puede enviarse el correo.",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="PENDIENTE"
    )
    ultimo_error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Correo en cola"
        verbose_name_plural = "Correos en cola"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.destinatario} - {self.asunto} ({self.estado})"
