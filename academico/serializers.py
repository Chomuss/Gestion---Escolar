from django.contrib.auth import get_user_model
from rest_framework import serializers

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

User = get_user_model()


# ============================================================
#  SERIALIZADORES COMPARTIDOS / BÁSICOS
# ============================================================

class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """
    Versión resumida del usuario para anidar en otros serializers.
    """
    full_name = serializers.SerializerMethodField()
    role_code = serializers.CharField(source="role.code", read_only=True)
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "rut",
            "role",
            "role_code",
            "role_display",
        )
        read_only_fields = ("id", "username", "role_code", "role_display")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_role_display(self, obj):
        return obj.role.get_code_display() if obj.role else None


class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    """
    Periodo académico con todos sus campos.
    """
    class Meta:
        model = PeriodoAcademico
        fields = "__all__"


class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = "__all__"


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = "__all__"


class RecursoSerializer(serializers.ModelSerializer):
    sala_detalle = SalaSerializer(source="sala", read_only=True)

    class Meta:
        model = Recurso
        fields = (
            "id",
            "nombre",
            "descripcion",
            "sala",
            "sala_detalle",
        )


# ============================================================
#  CURSOS
# ============================================================

class CursoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para cursos.
    - Escribe con IDs (periodo, jefe_curso, estudiantes).
    - Lee también detalle anidado.
    """
    periodo_detalle = PeriodoAcademicoSerializer(source="periodo", read_only=True)
    jefe_curso_detalle = UsuarioSimpleSerializer(source="jefe_curso", read_only=True)
    estudiantes_detalle = UsuarioSimpleSerializer(source="estudiantes", many=True, read_only=True)
    total_estudiantes = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = (
            "id",
            "nombre",
            "nivel",
            "capacidad_maxima",
            "periodo",
            "periodo_detalle",
            "jefe_curso",
            "jefe_curso_detalle",
            "estudiantes",
            "estudiantes_detalle",
            "total_estudiantes",
        )

    def get_total_estudiantes(self, obj):
        return obj.estudiantes.count() if obj.pk else 0


# ============================================================
#  BLOQUES HORARIOS Y HORARIOS DE CURSO
# ============================================================

class BloqueHorarioSerializer(serializers.ModelSerializer):
    periodo_detalle = PeriodoAcademicoSerializer(source="periodo", read_only=True)
    dia_semana_display = serializers.CharField(source="get_dia_semana_display", read_only=True)

    class Meta:
        model = BloqueHorario
        fields = (
            "id",
            "periodo",
            "periodo_detalle",
            "dia_semana",
            "dia_semana_display",
            "hora_inicio",
            "hora_fin",
        )


class HorarioCursoSerializer(serializers.ModelSerializer):
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    asignatura_detalle = AsignaturaSerializer(source="asignatura", read_only=True)
    docente_detalle = UsuarioSimpleSerializer(source="docente", read_only=True)
    sala_detalle = SalaSerializer(source="sala", read_only=True)
    bloque_detalle = BloqueHorarioSerializer(source="bloque", read_only=True)
    periodo_detalle = PeriodoAcademicoSerializer(source="periodo", read_only=True)

    class Meta:
        model = HorarioCurso
        fields = (
            "id",
            "curso",
            "curso_detalle",
            "asignatura",
            "asignatura_detalle",
            "docente",
            "docente_detalle",
            "sala",
            "sala_detalle",
            "bloque",
            "bloque_detalle",
            "periodo",
            "periodo_detalle",
            "es_rotativo",
        )


# ============================================================
#  ASISTENCIA
# ============================================================

class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    asignatura_detalle = AsignaturaSerializer(source="asignatura", read_only=True)
    registrado_por_detalle = UsuarioSimpleSerializer(source="registrado_por", read_only=True)

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Asistencia
        fields = (
            "id",
            "estudiante",
            "estudiante_detalle",
            "curso",
            "curso_detalle",
            "asignatura",
            "asignatura_detalle",
            "fecha",
            "estado",
            "estado_display",
            "motivo_inasistencia",
            "es_justificada",
            "registrado_por",
            "registrado_por_detalle",
            "fecha_registro",
        )
        read_only_fields = ("fecha_registro",)

    def validate(self, attrs):
        """
        Ejemplo de validación “profesional”:
        - Si la asistencia está marcada como JUSTIFICADA, debe venir un motivo.
        """
        estado = attrs.get("estado") or getattr(self.instance, "estado", None)
        motivo = attrs.get("motivo_inasistencia") or getattr(self.instance, "motivo_inasistencia", "")

        if estado == "JUSTIFICADO" and not motivo:
            raise serializers.ValidationError(
                {"motivo_inasistencia": "Debe especificar un motivo para una inasistencia justificada."}
            )
        return attrs


# ============================================================
#  EVALUACIONES Y CALIFICACIONES
# ============================================================

class EvaluacionSerializer(serializers.ModelSerializer):
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    asignatura_detalle = AsignaturaSerializer(source="asignatura", read_only=True)
    docente_detalle = UsuarioSimpleSerializer(source="docente", read_only=True)
    periodo_detalle = PeriodoAcademicoSerializer(source="periodo", read_only=True)

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    # Ejemplo de campo calculado: cantidad de calificaciones asociadas
    cantidad_calificaciones = serializers.SerializerMethodField()

    class Meta:
        model = Evaluacion
        fields = (
            "id",
            "curso",
            "curso_detalle",
            "asignatura",
            "asignatura_detalle",
            "docente",
            "docente_detalle",
            "periodo",
            "periodo_detalle",
            "titulo",
            "descripcion",
            "tipo",
            "tipo_display",
            "fecha_evaluacion",
            "fecha_limite_publicacion",
            "fecha_publicacion",
            "estado",
            "estado_display",
            "ponderacion",
            "creado_en",
            "actualizado_en",
            "cantidad_calificaciones",
        )
        read_only_fields = ("creado_en", "actualizado_en")

    def get_cantidad_calificaciones(self, obj):
        return obj.calificaciones.count()

    def validate(self, attrs):
        """
        Asegura que la fecha límite de publicación no sea menor a la fecha de evaluación.
        (Esto ya está en clean(), pero lo reforzamos a nivel de serializer para mejores mensajes).
        """
        fecha_eval = attrs.get("fecha_evaluacion") or getattr(self.instance, "fecha_evaluacion", None)
        fecha_limite = attrs.get("fecha_limite_publicacion") or getattr(
            self.instance, "fecha_limite_publicacion", None
        )

        if fecha_eval and fecha_limite and fecha_limite < fecha_eval:
            raise serializers.ValidationError(
                {"fecha_limite_publicacion": "La fecha límite no puede ser anterior a la fecha de evaluación."}
            )
        return attrs


class CalificacionSerializer(serializers.ModelSerializer):
    evaluacion_detalle = EvaluacionSerializer(source="evaluacion", read_only=True)
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)

    class Meta:
        model = Calificacion
        fields = (
            "id",
            "evaluacion",
            "evaluacion_detalle",
            "estudiante",
            "estudiante_detalle",
            "nota",
            "observaciones",
            "fecha_registro",
            "origen",
        )
        read_only_fields = ("fecha_registro",)

    def validate_nota(self, value):
        if value < 1.0 or value > 7.0:
            raise serializers.ValidationError("La nota debe estar en el rango 1.0 a 7.0.")
        return value


class PromedioFinalSerializer(serializers.ModelSerializer):
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    asignatura_detalle = AsignaturaSerializer(source="asignatura", read_only=True)
    periodo_detalle = PeriodoAcademicoSerializer(source="periodo", read_only=True)

    class Meta:
        model = PromedioFinal
        fields = (
            "id",
            "estudiante",
            "estudiante_detalle",
            "curso",
            "curso_detalle",
            "asignatura",
            "asignatura_detalle",
            "periodo",
            "periodo_detalle",
            "promedio",
            "aprobado",
            "fecha_calculo",
        )
        read_only_fields = ("fecha_calculo",)


# ============================================================
#  OBSERVACIONES, ALERTAS, INTERVENCIONES
# ============================================================

class ObservacionSerializer(serializers.ModelSerializer):
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)
    autor_detalle = UsuarioSimpleSerializer(source="autor", read_only=True)
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    asignatura_detalle = AsignaturaSerializer(source="asignatura", read_only=True)

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    gravedad_display = serializers.CharField(source="get_gravedad_display", read_only=True)

    class Meta:
        model = Observacion
        fields = (
            "id",
            "estudiante",
            "estudiante_detalle",
            "autor",
            "autor_detalle",
            "curso",
            "curso_detalle",
            "asignatura",
            "asignatura_detalle",
            "tipo",
            "tipo_display",
            "gravedad",
            "gravedad_display",
            "descripcion",
            "requiere_seguimiento",
            "fecha",
            "fecha_registro",
        )
        read_only_fields = ("fecha_registro",)


class AlertaTempranaSerializer(serializers.ModelSerializer):
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    creada_por_detalle = UsuarioSimpleSerializer(source="creada_por", read_only=True)

    origen_display = serializers.CharField(source="get_origen_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = AlertaTemprana
        fields = (
            "id",
            "estudiante",
            "estudiante_detalle",
            "curso",
            "curso_detalle",
            "origen",
            "origen_display",
            "descripcion",
            "nivel_riesgo",
            "estado",
            "estado_display",
            "creada_por",
            "creada_por_detalle",
            "fecha_creacion",
            "fecha_cierre",
        )
        read_only_fields = ("fecha_creacion",)


class IntervencionSerializer(serializers.ModelSerializer):
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)
    alerta_detalle = AlertaTempranaSerializer(source="alerta", read_only=True)
    observacion_detalle = ObservacionSerializer(source="observacion", read_only=True)
    responsable_detalle = UsuarioSimpleSerializer(source="responsable", read_only=True)

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Intervencion
        fields = (
            "id",
            "estudiante",
            "estudiante_detalle",
            "alerta",
            "alerta_detalle",
            "observacion",
            "observacion_detalle",
            "responsable",
            "responsable_detalle",
            "descripcion",
            "fecha",
            "estado",
            "estado_display",
            "resultado",
        )


# ============================================================
#  REUNIONES CON APODERADOS Y MINUTAS
# ============================================================

class ReunionApoderadosSerializer(serializers.ModelSerializer):
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)
    apoderado_detalle = UsuarioSimpleSerializer(source="apoderado", read_only=True)
    docente_detalle = UsuarioSimpleSerializer(source="docente", read_only=True)

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ReunionApoderados
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "curso",
            "curso_detalle",
            "estudiante",
            "estudiante_detalle",
            "apoderado",
            "apoderado_detalle",
            "docente",
            "docente_detalle",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "temas_tratados",
            "acuerdos",
            "observaciones",
            "creada_en",
        )
        read_only_fields = ("creada_en",)


class MinutaReunionSerializer(serializers.ModelSerializer):
    reunion_detalle = ReunionApoderadosSerializer(source="reunion", read_only=True)
    autor_detalle = UsuarioSimpleSerializer(source="autor", read_only=True)

    class Meta:
        model = MinutaReunion
        fields = (
            "id",
            "reunion",
            "reunion_detalle",
            "autor",
            "autor_detalle",
            "titulo",
            "resumen_general",
            "acuerdos_detallados",
            "compromisos_apoderados",
            "compromisos_establecimiento",
            "observaciones",
            "archivo_pdf",
            "creada_en",
            "actualizada_en",
        )
        read_only_fields = ("creada_en", "actualizada_en")


class AsistenciaReunionApoderadoSerializer(serializers.ModelSerializer):
    reunion_detalle = ReunionApoderadosSerializer(source="reunion", read_only=True)
    apoderado_detalle = UsuarioSimpleSerializer(source="apoderado", read_only=True)
    estudiante_detalle = UsuarioSimpleSerializer(source="estudiante", read_only=True)

    class Meta:
        model = AsistenciaReunionApoderado
        fields = (
            "id",
            "reunion",
            "reunion_detalle",
            "apoderado",
            "apoderado_detalle",
            "estudiante",
            "estudiante_detalle",
            "asistio",
            "justificacion",
            "temas_tratados",
            "fecha_registro",
        )
        read_only_fields = ("fecha_registro",)


# ============================================================
#  REPORTES, ADJUNTOS Y COLA DE CORREOS
# ============================================================

class ReporteNotasPeriodoSerializer(serializers.ModelSerializer):
    curso_detalle = CursoSerializer(source="curso", read_only=True)
    asignatura_detalle = AsignaturaSerializer(source="asignatura", read_only=True)
    periodo_detalle = PeriodoAcademicoSerializer(source="periodo", read_only=True)
    generado_por_detalle = UsuarioSimpleSerializer(source="generado_por", read_only=True)

    class Meta:
        model = ReporteNotasPeriodo
        fields = (
            "id",
            "curso",
            "curso_detalle",
            "asignatura",
            "asignatura_detalle",
            "periodo",
            "periodo_detalle",
            "generado_por",
            "generado_por_detalle",
            "fecha_generacion",
            "archivo_pdf",
            "archivo_excel",
        )
        read_only_fields = ("fecha_generacion",)


class ArchivoAdjuntoSerializer(serializers.ModelSerializer):
    subido_por_detalle = UsuarioSimpleSerializer(source="subido_por", read_only=True)

    class Meta:
        model = ArchivoAdjunto
        fields = (
            "id",
            "content_type",
            "object_id",
            "archivo",
            "descripcion",
            "subido_por",
            "subido_por_detalle",
            "fecha_subida",
        )
        read_only_fields = ("fecha_subida",)


class EmailQueueSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = EmailQueue
        fields = (
            "id",
            "destinatario",
            "asunto",
            "cuerpo",
            "creado_en",
            "enviar_despues_de",
            "estado",
            "estado_display",
            "ultimo_error",
        )
        read_only_fields = ("creado_en", "ultimo_error")
