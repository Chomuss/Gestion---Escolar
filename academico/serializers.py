from rest_framework import serializers
from django.utils import timezone

from usuarios.serializers import UserSerializer
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
#  AÑO Y PERIODO ACADÉMICO
# ============================================================

class AnioAcademicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnioAcademico
        fields = "__all__"


class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    anio = AnioAcademicoSerializer(read_only=True)

    class Meta:
        model = PeriodoAcademico
        fields = "__all__"


# ============================================================
#  NIVELES Y CURSOS
# ============================================================

class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nivel
        fields = "__all__"


class CursoSerializer(serializers.ModelSerializer):
    nivel = NivelSerializer(read_only=True)
    profesor_jefe = UserSerializer(read_only=True)

    total_estudiantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Curso
        fields = "__all__"


class CursoCreateUpdateSerializer(serializers.ModelSerializer):
    """Para crear/editar cursos, sin expandir información."""
    class Meta:
        model = Curso
        fields = "__all__"


# ============================================================
#  SALAS
# ============================================================

class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = "__all__"


# ============================================================
#  ASIGNATURAS
# ============================================================

class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = "__all__"


# ============================================================
#  ASIGNATURA – CURSO – DOCENTE
# ============================================================

class ACDSerializer(serializers.ModelSerializer):
    asignatura = AsignaturaSerializer(read_only=True)
    curso = CursoSerializer(read_only=True)
    docente = UserSerializer(read_only=True)

    class Meta:
        model = AsignaturaCursoDocente
        fields = "__all__"


class ACDCreateUpdateSerializer(serializers.ModelSerializer):
    """Para creación / edición"""
    class Meta:
        model = AsignaturaCursoDocente
        fields = "__all__"


# ============================================================
#  MATRÍCULA
# ============================================================

class MatriculaSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    curso = CursoSerializer(read_only=True)
    anio_academico = AnioAcademicoSerializer(read_only=True)

    class Meta:
        model = Matricula
        fields = "__all__"


class MatriculaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matricula
        fields = "__all__"


# ============================================================
#  HORARIO / BLOQUES
# ============================================================

class BloqueHorarioSerializer(serializers.ModelSerializer):
    asignacion = ACDSerializer(read_only=True)
    sala = SalaSerializer(read_only=True)

    dia_nombre = serializers.CharField(source="get_dia_semana_display", read_only=True)

    class Meta:
        model = BloqueHorario
        fields = "__all__"


class BloqueHorarioCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloqueHorario
        fields = "__all__"


# ============================================================
#  ASISTENCIA
# ============================================================

class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    curso = CursoSerializer(read_only=True)
    asignatura = AsignaturaSerializer(read_only=True)
    registrado_por = UserSerializer(read_only=True)

    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Asistencia
        fields = "__all__"


class AsistenciaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = "__all__"

    def validate(self, data):
        if data["fecha"] > timezone.now().date():
            raise serializers.ValidationError("La fecha no puede ser futura.")
        return data


# ============================================================
#  EVALUACIONES
# ============================================================

class EvaluacionSerializer(serializers.ModelSerializer):
    asignacion = ACDSerializer(read_only=True)
    periodo = PeriodoAcademicoSerializer(read_only=True)
    creado_por = UserSerializer(read_only=True)

    class Meta:
        model = Evaluacion
        fields = "__all__"


class EvaluacionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluacion
        fields = "__all__"

    def validate(self, data):
        if data["fecha"] > timezone.now().date():
            raise serializers.ValidationError("La fecha de la evaluación no puede ser futura.")
        if data["ponderacion"] <= 0:
            raise serializers.ValidationError("La ponderación debe ser mayor a cero.")
        return data


# ============================================================
#  CALIFICACIONES
# ============================================================

class CalificacionSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    evaluacion = EvaluacionSerializer(read_only=True)
    registrado_por = UserSerializer(read_only=True)

    porcentaje = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = Calificacion
        fields = "__all__"


class CalificacionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = "__all__"

    def validate(self, data):
        evaluacion = data["evaluacion"]
        puntaje = data["puntaje_obtenido"]

        if puntaje < 0:
            raise serializers.ValidationError("El puntaje no puede ser menor a 0.")
        if puntaje > evaluacion.puntaje_maximo:
            raise serializers.ValidationError("El puntaje excede el máximo permitido.")

        return data


# ============================================================
#  PROMEDIO FINAL
# ============================================================

class PromedioFinalSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    asignacion = ACDSerializer(read_only=True)
    periodo = PeriodoAcademicoSerializer(read_only=True)

    class Meta:
        model = PromedioFinal
        fields = "__all__"


class PromedioFinalCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromedioFinal
        fields = "__all__"


# ============================================================
#  OBSERVACIONES (DISCIPLINARIAS Y ACADÉMICAS)
# ============================================================

class ObservacionSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    curso = CursoSerializer(read_only=True)
    registrada_por = UserSerializer(read_only=True)

    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    gravedad_nombre = serializers.CharField(source="get_gravedad_display", read_only=True)

    class Meta:
        model = Observacion
        fields = "__all__"


class ObservacionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observacion
        fields = "__all__"


# ============================================================
#  CORREOS AUTOMÁTICOS (COLA DE ENVÍO)
# ============================================================

class EmailQueueSerializer(serializers.ModelSerializer):
    destinatario_usuario = UserSerializer(read_only=True)
    destinatario_curso = CursoSerializer(read_only=True)

    class Meta:
        model = EmailQueue
        fields = "__all__"


class EmailQueueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailQueue
        fields = "__all__"


# ============================================================
#  REUNIONES DE APODERADOS
# ============================================================

class ReunionApoderadosSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(read_only=True)
    docente = UserSerializer(read_only=True)

    class Meta:
        model = ReunionApoderados
        fields = "__all__"


class ReunionApoderadosCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReunionApoderados
        fields = "__all__"


class AsistenciaReunionSerializer(serializers.ModelSerializer):
    reunion = ReunionApoderadosSerializer(read_only=True)
    apoderado = UserSerializer(read_only=True)

    class Meta:
        model = AsistenciaReunionApoderado
        fields = "__all__"


class AsistenciaReunionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsistenciaReunionApoderado
        fields = "__all__"


# ============================================================
#  ALERTAS TEMPRANAS (RIESGO ACADÉMICO)
# ============================================================

class AlertaTempranaSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    curso = CursoSerializer(read_only=True)
    generada_por = UserSerializer(read_only=True)

    class Meta:
        model = AlertaTemprana
        fields = "__all__"


class AlertaTempranaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaTemprana
        fields = "__all__"


# ============================================================
#  REPORTE DE NOTAS POR PERIODO
# ============================================================

class ReporteNotasPeriodoSerializer(serializers.ModelSerializer):
    estudiante = UserSerializer(read_only=True)
    periodo = PeriodoAcademicoSerializer(read_only=True)

    class Meta:
        model = ReporteNotasPeriodo
        fields = "__all__"


class ReporteNotasPeriodoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteNotasPeriodo
        fields = "__all__"
