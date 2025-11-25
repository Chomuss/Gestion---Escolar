from django.contrib import admin

from .models import (
    AnioAcademico,
    PeriodoAcademico,
    Nivel,
    Curso,
    Sala,
    Asignatura,
    AsignaturaCursoDocente,
    Matricula,
    BloqueHorario,
    Asistencia,
    Evaluacion,
    Calificacion,
    PromedioFinal,
    Observacion,
    EmailQueue,
    ReunionApoderados,
    AsistenciaReunionApoderado,
    AlertaTemprana,
    ReporteNotasPeriodo,
)


# ============================================================
#  INLINES
# ============================================================

class MatriculaInline(admin.TabularInline):
    model = Matricula
    extra = 0
    autocomplete_fields = ("estudiante",)
    fields = ("estudiante", "estado", "fecha_matricula", "observacion")
    readonly_fields = ("fecha_matricula",)


class AsignaturaCursoDocenteInline(admin.TabularInline):
    model = AsignaturaCursoDocente
    extra = 0
    autocomplete_fields = ("asignatura", "docente")


class BloqueHorarioInline(admin.TabularInline):
    model = BloqueHorario
    extra = 0
    autocomplete_fields = ("sala",)
    fields = ("dia_semana", "hora_inicio", "hora_fin", "sala")


class AsistenciaReunionInline(admin.TabularInline):
    model = AsistenciaReunionApoderado
    extra = 0
    autocomplete_fields = ("apoderado",)
    fields = ("apoderado", "asistio", "observacion")


# ============================================================
#  AÑO / PERIODO ACADÉMICO
# ============================================================

@admin.register(AnioAcademico)
class AnioAcademicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)
    ordering = ("-fecha_inicio",)


@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "tipo", "orden", "fecha_inicio", "fecha_fin")
    list_filter = ("anio", "tipo")
    search_fields = ("nombre",)
    ordering = ("anio", "orden")


# ============================================================
#  NIVELES / CURSOS / SALAS
# ============================================================

@admin.register(Nivel)
class NivelAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio_academico", "nivel", "profesor_jefe", "total_estudiantes")
    list_filter = ("anio_academico", "nivel")
    search_fields = ("nombre", "profesor_jefe__first_name", "profesor_jefe__last_name")
    inlines = [MatriculaInline, AsignaturaCursoDocenteInline]


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion", "capacidad")
    search_fields = ("nombre", "ubicacion")


# ============================================================
#  ASIGNATURAS Y ASIGNACIONES
# ============================================================

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "horas_semanales", "activa")
    list_filter = ("activa",)
    search_fields = ("codigo", "nombre")


@admin.register(AsignaturaCursoDocente)
class AsignaturaCursoDocenteAdmin(admin.ModelAdmin):
    list_display = ("asignatura", "curso", "docente")
    list_filter = ("curso__anio_academico", "curso__nivel", "docente")
    search_fields = (
        "asignatura__nombre",
        "asignatura__codigo",
        "curso__nombre",
        "docente__first_name",
        "docente__last_name",
        "docente__username",
    )
    inlines = [BloqueHorarioInline]


# ============================================================
#  MATRÍCULAS
# ============================================================

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "curso", "anio_academico", "estado", "fecha_matricula")
    list_filter = ("anio_academico", "estado", "curso__nivel")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
        "curso__nombre",
    )
    autocomplete_fields = ("estudiante", "curso", "anio_academico")


# ============================================================
#  HORARIOS
# ============================================================

@admin.register(BloqueHorario)
class BloqueHorarioAdmin(admin.ModelAdmin):
    list_display = ("asignacion", "dia_semana", "hora_inicio", "hora_fin", "sala")
    list_filter = ("dia_semana", "asignacion__curso", "asignacion__asignatura")
    search_fields = (
        "asignacion__asignatura__nombre",
        "asignacion__curso__nombre",
        "sala__nombre",
    )
    autocomplete_fields = ("asignacion", "sala")


# ============================================================
#  ASISTENCIA
# ============================================================

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "estudiante", "curso", "asignatura", "estado", "registrado_por")
    list_filter = ("fecha", "estado", "curso", "asignatura")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
        "curso__nombre",
        "asignatura__nombre",
    )
    autocomplete_fields = ("estudiante", "curso", "asignatura", "registrado_por")
    readonly_fields = ("creado_en",)


# ============================================================
#  EVALUACIONES / CALIFICACIONES / PROMEDIOS
# ============================================================

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "asignacion", "tipo", "fecha", "ponderacion", "creado_por")
    list_filter = ("tipo", "fecha", "asignacion__curso", "asignacion__asignatura", "periodo")
    search_fields = ("titulo", "descripcion", "asignacion__asignatura__nombre", "asignacion__curso__nombre")
    autocomplete_fields = ("asignacion", "periodo", "creado_por")
    readonly_fields = ("creado_en",)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("evaluacion", "estudiante", "puntaje_obtenido", "porcentaje", "registrado_por", "registrado_en")
    list_filter = ("evaluacion__asignacion__curso", "evaluacion__asignacion__asignatura")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
        "evaluacion__titulo",
    )
    autocomplete_fields = ("evaluacion", "estudiante", "registrado_por")
    readonly_fields = ("registrado_en",)


@admin.register(PromedioFinal)
class PromedioFinalAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "asignacion", "periodo", "promedio", "calculado_en")
    list_filter = ("periodo", "asignacion__curso", "asignacion__asignatura")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
        "asignacion__asignatura__nombre",
        "asignacion__curso__nombre",
    )
    autocomplete_fields = ("estudiante", "asignacion", "periodo")
    readonly_fields = ("calculado_en",)


# ============================================================
#  OBSERVACIONES
# ============================================================

@admin.register(Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    list_display = ("fecha", "estudiante", "tipo", "gravedad", "curso", "resuelta")
    list_filter = ("tipo", "gravedad", "resuelta", "curso")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
        "descripcion",
    )
    autocomplete_fields = ("estudiante", "curso", "registrada_por")
    readonly_fields = ("resuelta_en",)


# ============================================================
#  EMAIL QUEUE
# ============================================================

@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ("asunto", "tipo_destinatario", "destinatario_usuario", "destinatario_curso", "enviado", "creado_en", "enviado_en")
    list_filter = ("tipo_destinatario", "enviado")
    search_fields = ("asunto", "contenido", "destinatario_usuario__username", "destinatario_curso__nombre")
    autocomplete_fields = ("destinatario_usuario", "destinatario_curso")
    readonly_fields = ("creado_en", "enviado_en")


# ============================================================
#  REUNIONES DE APODERADOS
# ============================================================

@admin.register(ReunionApoderados)
class ReunionApoderadosAdmin(admin.ModelAdmin):
    list_display = ("curso", "docente", "fecha", "tema", "creada_en")
    list_filter = ("curso", "docente", "fecha")
    search_fields = ("tema", "descripcion", "curso__nombre", "docente__username", "docente__first_name", "docente__last_name")
    autocomplete_fields = ("curso", "docente")
    readonly_fields = ("creada_en",)
    inlines = [AsistenciaReunionInline]


@admin.register(AsistenciaReunionApoderado)
class AsistenciaReunionApoderadoAdmin(admin.ModelAdmin):
    list_display = ("reunion", "apoderado", "asistio")
    list_filter = ("asistio", "reunion__curso")
    search_fields = (
        "apoderado__username",
        "apoderado__first_name",
        "apoderado__last_name",
        "reunion__tema",
    )
    autocomplete_fields = ("reunion", "apoderado")
    

# ============================================================
#  ALERTAS TEMPRANAS
# ============================================================

@admin.register(AlertaTemprana)
class AlertaTempranaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "curso", "nivel", "motivo", "fecha", "notificada")
    list_filter = ("nivel", "notificada", "curso")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
        "motivo",
        "descripcion",
    )
    autocomplete_fields = ("estudiante", "curso", "generada_por")
    readonly_fields = ("fecha",)


# ============================================================
#  REPORTES POR PERIODO
# ============================================================

@admin.register(ReporteNotasPeriodo)
class ReporteNotasPeriodoAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "periodo", "promedio_general", "generado_en")
    list_filter = ("periodo__anio", "periodo")
    search_fields = (
        "estudiante__username",
        "estudiante__first_name",
        "estudiante__last_name",
    )
    autocomplete_fields = ("estudiante", "periodo")
    readonly_fields = ("generado_en",)
