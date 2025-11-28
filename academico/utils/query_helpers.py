from datetime import date
from typing import Optional

from django.db.models import QuerySet

from academico.models import (
    Asistencia,
    Calificacion,
    Evaluacion,
    Curso,
    Asignatura,
    PeriodoAcademico,
    PromedioFinal,
)
from usuarios.models import User


# ============================================================
#  CONSULTAS OPTIMIZADAS PARA REPORTES
# ============================================================

def obtener_calificaciones_curso_asignatura_periodo(
    curso: Curso,
    asignatura: Asignatura,
    periodo: PeriodoAcademico,
) -> QuerySet[Calificacion]:
    """
    Retorna un queryset optimizado de Calificacion para:
      - curso
      - asignatura
      - periodo

    Incluye select_related necesarios para evitar N+1 queries.
    """
    return (
        Calificacion.objects
        .select_related(
            "estudiante",
            "evaluacion",
            "evaluacion__curso",
            "evaluacion__asignatura",
            "evaluacion__periodo",
        )
        .filter(
            evaluacion__curso=curso,
            evaluacion__asignatura=asignatura,
            evaluacion__periodo=periodo,
        )
    )


def obtener_asistencias_estudiante_rango(
    estudiante: User,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    curso: Optional[Curso] = None,
) -> QuerySet[Asistencia]:
    """
    Retorna un queryset de asistencias de un estudiante, con filtros
    opcionales por curso y rango de fechas.
    """
    qs = (
        Asistencia.objects
        .select_related("curso", "asignatura", "estudiante")
        .filter(estudiante=estudiante)
    )

    if curso:
        qs = qs.filter(curso=curso)

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    return qs


def obtener_cursos_con_relaciones_basicas() -> QuerySet[Curso]:
    """
    Retorna cursos con relaciones comunes precargadas:
      - periodo
      - jefe_curso
      - estudiantes (prefetch)
    """
    return (
        Curso.objects
        .select_related("periodo", "jefe_curso")
        .prefetch_related("estudiantes")
    )


def obtener_promedios_finales_estudiante(
    estudiante: User,
    periodo: Optional[PeriodoAcademico] = None,
) -> QuerySet[PromedioFinal]:
    """
    Retorna los PromedioFinal de un estudiante, opcionalmente filtrados
    por un período.
    """
    qs = (
        PromedioFinal.objects
        .select_related("curso", "asignatura", "periodo")
        .filter(estudiante=estudiante)
    )

    if periodo:
        qs = qs.filter(periodo=periodo)

    return qs


def obtener_evaluaciones_curso_asignatura(
    curso: Curso,
    asignatura: Optional[Asignatura] = None,
    periodo: Optional[PeriodoAcademico] = None,
) -> QuerySet[Evaluacion]:
    """
    Retorna evaluaciones de un curso, con filtros opcionales por asignatura y período.
    """
    qs = (
        Evaluacion.objects
        .select_related("curso", "asignatura", "docente", "periodo")
        .filter(curso=curso)
    )

    if asignatura:
        qs = qs.filter(asignatura=asignatura)

    if periodo:
        qs = qs.filter(periodo=periodo)

    return qs
