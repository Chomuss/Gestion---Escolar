from django_filters import rest_framework as filters

from .models import (
    Curso,
    Asignatura,
    Asistencia,
    PromedioFinal,
    AlertaTemprana,
    Evaluacion,
)


class CursoFilter(filters.FilterSet):
    """
    Filtros para cursos:
    - periodo: por id de período académico
    - anio: por año del período
    - tipo_periodo: tipo del período (ANUAL, SEMESTRAL, etc.)
    - nivel: nivel educativo (icontains)
    - nombre: nombre del curso (icontains)
    - jefe_curso: por id de usuario jefe de curso
    """

    periodo = filters.NumberFilter(field_name="periodo_id")
    anio = filters.NumberFilter(field_name="periodo__anio")
    tipo_periodo = filters.CharFilter(field_name="periodo__tipo", lookup_expr="iexact")
    nivel = filters.CharFilter(field_name="nivel", lookup_expr="icontains")
    nombre = filters.CharFilter(field_name="nombre", lookup_expr="icontains")
    jefe_curso = filters.NumberFilter(field_name="jefe_curso_id")
    jefe_curso_rut = filters.CharFilter(field_name="jefe_curso__rut", lookup_expr="icontains")

    class Meta:
        model = Curso
        fields = [
            "periodo",
            "anio",
            "tipo_periodo",
            "nivel",
            "nombre",
            "jefe_curso",
        ]


class AsignaturaFilter(filters.FilterSet):
    """
    Filtros básicos para asignaturas:
    - nombre: búsqueda por nombre
    - codigo: búsqueda por código
    - tipo: tipo de asignatura (NORMAL, TALLER, etc.)
    """

    nombre = filters.CharFilter(field_name="nombre", lookup_expr="icontains")
    codigo = filters.CharFilter(field_name="codigo", lookup_expr="icontains")
    tipo = filters.CharFilter(field_name="tipo", lookup_expr="iexact")

    class Meta:
        model = Asignatura
        fields = ["nombre", "codigo", "tipo"]


class AsistenciaFilter(filters.FilterSet):
    """
    Filtros para asistencia:
    - curso, asignatura, estudiante
    - estado (PRESENTE, AUSENTE, ATRASO, JUSTIFICADO)
    - es_justificada (True/False)
    - rango de fechas (fecha_desde, fecha_hasta)
    - mes y año de la fecha (mes, anio)
    """

    curso = filters.NumberFilter(field_name="curso_id")
    asignatura = filters.NumberFilter(field_name="asignatura_id")
    estudiante = filters.NumberFilter(field_name="estudiante_id")

    estado = filters.CharFilter(field_name="estado", lookup_expr="iexact")
    es_justificada = filters.BooleanFilter(field_name="es_justificada")

    fecha_desde = filters.DateFilter(field_name="fecha", lookup_expr="gte")
    fecha_hasta = filters.DateFilter(field_name="fecha", lookup_expr="lte")

    # Aquí está el filtro por MES y AÑO
    mes = filters.NumberFilter(field_name="fecha", lookup_expr="month")
    anio = filters.NumberFilter(field_name="fecha", lookup_expr="year")

    class Meta:
        model = Asistencia
        fields = [
            "curso",
            "asignatura",
            "estudiante",
            "estado",
            "es_justificada",
            "fecha_desde",
            "fecha_hasta",
            "mes",
            "anio",
        ]


class PromedioFinalFilter(filters.FilterSet):
    """
    Filtros para promedios finales:
    - curso, asignatura, periodo, estudiante
    - aprobado (True/False)
    - promedio_min / promedio_max (rango de promedio)
    """

    curso = filters.NumberFilter(field_name="curso_id")
    asignatura = filters.NumberFilter(field_name="asignatura_id")
    periodo = filters.NumberFilter(field_name="periodo_id")
    estudiante = filters.NumberFilter(field_name="estudiante_id")

    aprobado = filters.BooleanFilter(field_name="aprobado")

    # Aquí está el filtro por PROMEDIO
    promedio_min = filters.NumberFilter(field_name="promedio", lookup_expr="gte")
    promedio_max = filters.NumberFilter(field_name="promedio", lookup_expr="lte")

    class Meta:
        model = PromedioFinal
        fields = [
            "curso",
            "asignatura",
            "periodo",
            "estudiante",
            "aprobado",
            "promedio_min",
            "promedio_max",
        ]


class AlertaTempranaFilter(filters.FilterSet):
    """
    Filtros para alertas tempranas:
    - curso, asignatura, estudiante
    - origen (ASISTENCIA, NOTAS, DISCIPLINA, MIXTO)
    - nivel_riesgo (BAJO, MEDIO, ALTO)
    - estado (ABIERTA, EN_SEGUIMIENTO, CERRADA)
    - solo_abiertas (True => fuerza estado=ABIERTA)
    - periodo: filtra por periodo del curso relacionado
    - fecha_desde / fecha_hasta: rango por fecha_creacion
    """

    curso = filters.NumberFilter(field_name="curso_id")
    asignatura = filters.NumberFilter(field_name="asignatura_id")
    estudiante = filters.NumberFilter(field_name="estudiante_id")

    origen = filters.CharFilter(field_name="origen", lookup_expr="iexact")
    nivel_riesgo = filters.CharFilter(field_name="nivel_riesgo", lookup_expr="iexact")
    estado = filters.CharFilter(field_name="estado", lookup_expr="iexact")

    # Aquí está el filtro de "alertas abiertas"
    solo_abiertas = filters.BooleanFilter(method="filter_solo_abiertas")

    # Filtrar por período del curso asociado
    periodo = filters.NumberFilter(method="filter_periodo")

    fecha_desde = filters.DateTimeFilter(field_name="fecha_creacion", lookup_expr="gte")
    fecha_hasta = filters.DateTimeFilter(field_name="fecha_creacion", lookup_expr="lte")

    class Meta:
        model = AlertaTemprana
        fields = [
            "curso",
            "asignatura",
            "estudiante",
            "origen",
            "nivel_riesgo",
            "estado",
        ]

    def filter_solo_abiertas(self, queryset, name, value):
        if value:
            return queryset.filter(estado="ABIERTA")
        return queryset

    def filter_periodo(self, queryset, name, value):
        if not value:
            return queryset
        # Filtra por periodo del curso asociado
        return queryset.filter(curso__periodo_id=value)


class EvaluacionFilter(filters.FilterSet):
    """
    Filtros para evaluaciones:
    - curso, asignatura, docente, periodo
    - estado (PENDIENTE, ATRASADA, PUBLICADA)
    - rango de fechas (fecha_desde, fecha_hasta)
    """

    curso = filters.NumberFilter(field_name="curso_id")
    asignatura = filters.NumberFilter(field_name="asignatura_id")
    docente = filters.NumberFilter(field_name="docente_id")
    periodo = filters.NumberFilter(field_name="periodo_id")

    estado = filters.CharFilter(field_name="estado", lookup_expr="iexact")

    fecha_desde = filters.DateFilter(field_name="fecha_evaluacion", lookup_expr="gte")
    fecha_hasta = filters.DateFilter(field_name="fecha_evaluacion", lookup_expr="lte")

    class Meta:
        model = Evaluacion
        fields = [
            "curso",
            "asignatura",
            "docente",
            "periodo",
            "estado",
            "fecha_desde",
            "fecha_hasta",
        ]
