from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from usuarios.models import User
from academico.models import (
    Curso,
    Asignatura,
    Asistencia,
    Calificacion,
    Observacion,
    Evaluacion,
    AlertaTemprana, 
    ReporteNotasPeriodo
)


# ============================================================
#  USUARIO
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Usuario ejemplo",
            value={
                "id": 12,
                "username": "jperez",
                "first_name": "Juan",
                "last_name": "Pérez",
                "email": "jperez@example.com",
                "role": "ALUMNO",
            }
        )
    ]
)
class UsuarioSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.code")

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role"]
        read_only_fields = fields


# ============================================================
#  CURSO
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Curso básico",
            value={
                "id": 3,
                "nombre": "1° Básico A",
                "nivel": "Educación Básica",
                "anio_academico": 2025,
                "profesor_jefe": 7,
            }
        )
    ]
)
class CursoSerializer(serializers.ModelSerializer):
    nivel = serializers.CharField(source="nivel.nombre")

    class Meta:
        model = Curso
        fields = [
            "id",
            "nombre",
            "nivel",
            "anio_academico",
            "profesor_jefe",
        ]
        read_only_fields = fields


# ============================================================
#  ASIGNATURA
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Asignatura Matemáticas",
            value={
                "id": 1,
                "codigo": "MAT01",
                "nombre": "Matemáticas",
                "descripcion": "Curso base de matemáticas",
            }
        )
    ]
)
class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = ["id", "codigo", "nombre", "descripcion"]
        read_only_fields = fields


# ============================================================
#  ASISTENCIA
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Asistencia ejemplo",
            value={
                "id": 100,
                "fecha": "2025-05-12",
                "estado": "PRESENTE",
                "asignatura": 2,
                "curso": 5,
                "estudiante": {
                    "id": 12,
                    "username": "jperez",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "jperez@example.com",
                    "role": "ALUMNO",
                }
            }
        )
    ]
)
class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante = UsuarioSerializer()

    class Meta:
        model = Asistencia
        fields = [
            "id",
            "fecha",
            "estado",
            "asignatura",
            "curso",
            "estudiante",
        ]
        read_only_fields = fields


# ============================================================
#  CALIFICACIONES
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Calificación ejemplo",
            value={
                "id": 55,
                "estudiante": {
                    "id": 12,
                    "username": "jperez",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "jperez@example.com",
                    "role": "ALUMNO",
                },
                "evaluacion": 8,
                "puntaje_obtenido": 6.5,
                "porcentaje": 65.0,
                "registrado_en": "2025-05-14T12:12:00Z",
            }
        )
    ]
)
class CalificacionSerializer(serializers.ModelSerializer):
    estudiante = UsuarioSerializer()

    class Meta:
        model = Calificacion
        fields = [
            "id",
            "estudiante",
            "evaluacion",
            "puntaje_obtenido",
            "porcentaje",
            "registrado_en",
        ]
        read_only_fields = fields


# ============================================================
#  OBSERVACIONES
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Observación disciplinaria",
            value={
                "id": 3,
                "tipo": "DISCIPLINARIA",
                "gravedad": "MEDIA",
                "descripcion": "Interrupción constante de la clase.",
                "fecha": "2025-04-10",
                "curso": 5,
                "estudiante": {
                    "id": 12,
                    "username": "jperez",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "jperez@example.com",
                    "role": "ALUMNO",
                }
            }
        )
    ]
)
class ObservacionSerializer(serializers.ModelSerializer):
    estudiante = UsuarioSerializer()

    class Meta:
        model = Observacion
        fields = [
            "id",
            "tipo",
            "gravedad",
            "descripcion",
            "fecha",
            "estudiante",
            "curso",
        ]
        read_only_fields = fields


# ============================================================
#  EVALUACIONES
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Evaluación ejemplo",
            value={
                "id": 8,
                "titulo": "Prueba Unidad 1",
                "tipo": "PRUEBA",
                "fecha": "2025-05-15",
                "asignacion": 14,
                "ponderacion": 25.0,
            }
        )
    ]
)
class EvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluacion
        fields = [
            "id",
            "titulo",
            "tipo",
            "fecha",
            "asignacion",
            "ponderacion",
        ]
        read_only_fields = fields


# ============================================================
#  ALERTAS TEMPRANAS
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Alerta temprana",
            value={
                "id": 4,
                "estudiante": {
                    "id": 12,
                    "username": "jperez",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "jperez@example.com",
                    "role": "ALUMNO",
                },
                "curso": 5,
                "nivel": "ALTO",
                "motivo": "Bajo rendimiento en dos asignaturas",
                "descripcion": "Promedio inferior a 4.0",
                "fecha": "2025-06-10T10:00:00Z",
            }
        )
    ]
)
class AlertaTempranaSerializer(serializers.ModelSerializer):
    estudiante = UsuarioSerializer()

    class Meta:
        model = AlertaTemprana
        fields = [
            "id",
            "estudiante",
            "curso",
            "nivel",
            "motivo",
            "descripcion",
            "fecha",
        ]
        read_only_fields = fields


# ============================================================
#  REPORTE POR PERIODO
# ============================================================

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Reporte periodo ejemplo",
            value={
                "id": 1,
                "estudiante": {
                    "id": 12,
                    "username": "jperez",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "jperez@example.com",
                    "role": "ALUMNO",
                },
                "periodo": 2,
                "promedio_general": 5.2,
                "generado_en": "2025-06-30T18:30:00Z",
            }
        )
    ]
)
class ReportePeriodoSerializer(serializers.ModelSerializer):
    estudiante = UsuarioSerializer()

    class Meta:
        model = ReporteNotasPeriodo
        fields = [
            "id",
            "estudiante",
            "periodo",
            "promedio_general",
            "generado_en",
        ]
        read_only_fields = fields
