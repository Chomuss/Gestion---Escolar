from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import (
    PeriodoAcademico,
    Curso,
    Asignatura,
    Sala,
    Recurso,
    BloqueHorario,
    HorarioCurso,
    Asistencia,
    Evaluacion,
    Calificacion,
    PromedioFinal,
    Observacion,
    AlertaTemprana,
    Intervencion,
    ReunionApoderados,
    MinutaReunion,
    AsistenciaReunionApoderado,
    ReporteNotasPeriodo,
    ArchivoAdjunto,
    EmailQueue,
)


# ============================================================
#  INLINES
# ============================================================

class HorarioCursoInline(admin.TabularInline):
    model = HorarioCurso
    extra = 0
    autocomplete_fields = ("asignatura", "docente", "sala", "bloque")
    show_change_link = True


class MinutaReunionInline(admin.StackedInline):
    model = MinutaReunion
    extra = 0
    show_change_link = True


class AsistenciaReunionInline(admin.TabularInline):
    model = AsistenciaReunionApoderado
    extra = 0
    autocomplete_fields = ("apoderado", "estudiante")


class ArchivoAdjuntoInline(GenericTabularInline):
    """
    Inline genérico para adjuntar archivos a observaciones,
    intervenciones, reuniones, etc.
    """
    model = ArchivoAdjunto
    extra = 0


# ============================================================
#  PERÍODOS ACADÉMICOS
# ============================================================

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "tipo", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("tipo", "anio", "activo")
    search_fields = ("nombre",)
    ordering = ("-anio", "-fecha_inicio")
    list_editable = ("activo",)


# ============================================================
#  CURSOS
# ============================================================

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nivel", "periodo", "jefe_curso", "capacidad_maxima", "total_estudiantes")
    list_filter = ("periodo", "nivel")
    search_fields = ("nombre", "nivel", "jefe_curso__first_name", "jefe_curso__last_name", "jefe_curso__rut")
    ordering = ("nivel", "nombre")
    autocomplete_fields = ("periodo", "jefe_curso")
    filter_horizontal = ("estudiantes",)
    inlines = [HorarioCursoInline]

    def total_estudiantes(self, obj):
        return obj.estudiantes.count()
    total_estudiantes.short_description = "Nº estudiantes"


# ============================================================
#  ASIGNATURAS
# ============================================================

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "tipo", "carga_horaria_semanal")
    list_filter = ("tipo",)
    search_fields = ("nombre", "codigo")
    ordering = ("nombre",)


# ============================================================
#  SALAS Y RECURSOS
# ============================================================

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "tipo", "capacidad", "ubicacion")
    list_filter = ("tipo",)
    search_fields = ("nombre", "codigo", "ubicacion")
    ordering = ("nombre",)


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sala", "activo")
    list_filter = ("activo", "sala")
    search_fields = ("nombre", "sala__nombre")
    autocomplete_fields = ("sala",)
    ordering = ("nombre",)


# ============================================================
#  BLOQUES HORARIOS Y HORARIOS DE CURSO
# ============================================================

@admin.register(BloqueHorario)
class BloqueHorarioAdmin(admin.ModelAdmin):
    list_display = ("periodo", "dia_semana", "hora_inicio", "hora_fin")
    list_filter = ("periodo", "dia_semana")
    search_fields = ("periodo__nombre",)
    ordering = ("periodo", "dia_semana", "hora_inicio")
    autocomplete_fields = ("periodo",)


@admin.register(HorarioCurso)
class HorarioCursoAdmin(admin.ModelAdmin):
    list_display = ("curso", "asignatura", "docente", "sala", "bloque", "periodo", "es_rotativo")
    list_filter = ("periodo", "curso", "asignatura", "docente", "sala", "es_rotativo")
    search_fields = (
        "curso__nombre",
        "asignatura__nombre",
        "docente__first_name",
        "docente__last_name",
    )
    autocomplete_fields = ("curso", "asignatura", "docente", "sala", "bloque", "periodo")
    ordering = ("curso", "bloque__dia_semana", "bloque__hora_inicio")


# ============================================================
#  ASISTENCIA
# ============================================================

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "curso",
        "asignatura",
        "estudiante",
        "estado",
        "es_justificada",
        "registrado_por",
    )
    list_filter = ("estado", "es_justificada", "curso", "asignatura")
    search_fields = (
        "estudiante__first_name",
        "estudiante__last_name",
        "estudiante__rut",
        "curso__nombre",
        "asignatura__nombre",
    )
    autocomplete_fields = ("estudiante", "curso", "asignatura", "registrado_por")
    date_hierarchy = "fecha"
    ordering = ("-fecha", "curso__nombre")


# ============================================================
#  EVALUACIONES Y CALIFICACIONES
# ============================================================

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "curso",
        "asignatura",
        "docente",
        "tipo",
        "fecha_evaluacion",
        "fecha_limite_publicacion",
        "estado",
        "ponderacion",
    )
    list_filter = ("periodo", "curso", "asignatura", "docente", "tipo", "estado")
    search_fields = (
        "titulo",
        "curso__nombre",
        "asignatura__nombre",
        "docente__first_name",
        "docente__last_name",
    )
    autocomplete_fields = ("curso", "asignatura", "docente", "periodo")
    ordering = ("-fecha_evaluacion",)
    list_editable = ("estado",)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("evaluacion", "estudiante", "nota", "origen", "fecha_registro")
    list_filter = ("origen", "evaluacion__curso", "evaluacion__asignatura")
    search_fields = (
        "estudiante__first_name",
        "estudiante__last_name",
        "estudiante__rut",
        "evaluacion__titulo",
        "evaluacion__curso__nombre",
    )
    autocomplete_fields = ("evaluacion", "estudiante")
    date_hierarchy = "fecha_registro"
    ordering = ("-fecha_registro",)


@admin.register(PromedioFinal)
class PromedioFinalAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "curso", "asignatura", "periodo", "promedio", "aprobado", "fecha_calculo")
    list_filter = ("periodo", "curso", "asignatura", "aprobado")
    search_fields = (
        "estudiante__first_name",
        "estudiante__last_name",
        "estudiante__rut",
        "curso__nombre",
        "asignatura__nombre",
    )
    autocomplete_fields = ("estudiante", "curso", "asignatura", "periodo")
    ordering = ("-fecha_calculo",)


# ============================================================
#  OBSERVACIONES, ALERTAS, INTERVENCIONES
# ============================================================

@admin.register(Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "curso", "tipo", "gravedad", "requiere_seguimiento", "fecha")
    list_filter = ("tipo", "gravedad", "requiere_seguimiento", "curso")
    search_fields = (
        "estudiante__first_name",
        "estudiante__last_name",
        "estudiante__rut",
        "descripcion",
    )
    autocomplete_fields = ("estudiante", "autor", "curso")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)
    inlines = [ArchivoAdjuntoInline]


@admin.register(AlertaTemprana)
class AlertaTempranaAdmin(admin.ModelAdmin):
    list_display = (
        "estudiante",
        "curso",
        "origen",
        "nivel_riesgo",
        "estado",
        "creada_por",
        "fecha_creacion",
        "fecha_cierre",
    )
    list_filter = ("origen", "nivel_riesgo", "estado", "curso")
    search_fields = (
        "estudiante__first_name",
        "estudiante__last_name",
        "estudiante__rut",
        "descripcion",
    )
    autocomplete_fields = ("estudiante", "curso", "creada_por")
    date_hierarchy = "fecha_creacion"
    ordering = ("-fecha_creacion",)


@admin.register(Intervencion)
class IntervencionAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "alerta", "observacion", "responsable", "estado", "fecha")
    list_filter = ("estado", "responsable", "alerta")
    search_fields = (
        "estudiante__first_name",
        "estudiante__last_name",
        "estudiante__rut",
        "descripcion",
    )
    autocomplete_fields = ("estudiante", "alerta", "observacion", "responsable")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)
    inlines = [ArchivoAdjuntoInline]


# ============================================================
#  REUNIONES CON APODERADOS
# ============================================================

@admin.register(ReunionApoderados)
class ReunionApoderadosAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "curso",
        "estudiante",
        "apoderado",
        "docente",
        "fecha",
        "hora_inicio",
        "hora_fin",
    )
    list_filter = ("tipo", "curso", "docente")
    search_fields = (
        "curso__nombre",
        "estudiante__first_name",
        "estudiante__last_name",
        "apoderado__first_name",
        "apoderado__last_name",
    )
    autocomplete_fields = ("curso", "estudiante", "apoderado", "docente")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)
    inlines = [MinutaReunionInline, AsistenciaReunionInline, ArchivoAdjuntoInline]


# ============================================================
#  REPORTES DE NOTAS
# ============================================================

@admin.register(ReporteNotasPeriodo)
class ReporteNotasPeriodoAdmin(admin.ModelAdmin):
    list_display = ("curso", "asignatura", "periodo", "generado_por", "fecha_generacion")
    list_filter = ("periodo", "curso", "asignatura")
    search_fields = ("curso__nombre", "asignatura__nombre", "periodo__nombre")
    autocomplete_fields = ("curso", "asignatura", "periodo", "generado_por")
    date_hierarchy = "fecha_generacion"
    ordering = ("-fecha_generacion",)


# ============================================================
#  ARCHIVOS ADJUNTOS GENÉRICOS
# ============================================================

@admin.register(ArchivoAdjunto)
class ArchivoAdjuntoAdmin(admin.ModelAdmin):
    list_display = ("archivo", "content_type", "object_id", "subido_por", "fecha_subida")
    list_filter = ("content_type", "subido_por")
    search_fields = ("archivo", "descripcion")
    autocomplete_fields = ("subido_por",)
    date_hierarchy = "fecha_subida"
    ordering = ("-fecha_subida",)


# ============================================================
#  COLA DE EMAILS
# ============================================================

@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ("destinatario", "asunto", "estado", "creado_en", "enviar_despues_de", "ultimo_error_resumido")
    list_filter = ("estado",)
    search_fields = ("destinatario", "asunto", "cuerpo")
    date_hierarchy = "creado_en"
    ordering = ("-creado_en",)

    readonly_fields = ("creado_en", "ultimo_error")

    def ultimo_error_resumido(self, obj):
        if not obj.ultimo_error:
            return ""
        return (obj.ultimo_error[:75] + "...") if len(obj.ultimo_error) > 75 else obj.ultimo_error
    ultimo_error_resumido.short_description = "Último error"
