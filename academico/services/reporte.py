# academico/services/reporte.py

import csv
import io
from decimal import Decimal
from typing import Optional

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Avg, Min, Max, Count

from academico.models import (
    Curso,
    Asignatura,
    PeriodoAcademico,
    Calificacion,
    ReporteNotasPeriodo,
    PromedioFinal,
)


@transaction.atomic
def generar_reporte_notas_curso_asignatura_periodo(
    curso: Curso,
    asignatura: Asignatura,
    periodo: PeriodoAcademico,
    generado_por=None,
) -> Optional[ReporteNotasPeriodo]:
    """
    Genera o actualiza un ReporteNotasPeriodo para un curso + asignatura + período.

    - Calcula estadísticas globales de notas.
    - Calcula promedios por estudiante y actualiza/crea PromedioFinal.
    - Genera un archivo CSV (compatible con Excel) y lo guarda en archivo_excel.
    """
    calificaciones_qs = Calificacion.objects.filter(
        evaluacion__curso=curso,
        evaluacion__asignatura=asignatura,
        evaluacion__periodo=periodo,
    )

    if not calificaciones_qs.exists():
        return None

    # 1) Obtener/crear el reporte
    reporte, _created = ReporteNotasPeriodo.objects.get_or_create(
        curso=curso,
        asignatura=asignatura,
        periodo=periodo,
        defaults={"generado_por": generado_por},
    )

    if not _created and generado_por is not None:
        reporte.generado_por = generado_por
        reporte.save(update_fields=["generado_por"])

    # 2) Estadísticas globales
    stats_globales = calificaciones_qs.aggregate(
        promedio=Avg("nota"),
        minima=Min("nota"),
        maxima=Max("nota"),
        cantidad=Count("id"),
    )

    # 3) Promedios por estudiante (y actualización de PromedioFinal)
    promedios_por_estudiante = (
        calificaciones_qs
        .values("estudiante", "evaluacion__curso", "evaluacion__asignatura")
        .annotate(
            promedio=Avg("nota"),
            minima=Min("nota"),
            maxima=Max("nota"),
            cantidad=Count("id"),
        )
    )

    # 4) Construir CSV en memoria
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')

    # Encabezado de resumen
    writer.writerow(["RESUMEN GLOBAL"])
    writer.writerow([
        "Curso",
        "Asignatura",
        "Periodo",
        "Cantidad notas",
        "Nota mínima",
        "Nota máxima",
        "Promedio",
    ])

    writer.writerow([
        str(curso),
        str(asignatura),
        str(periodo),
        stats_globales["cantidad"],
        f"{stats_globales['minima']:.2f}",
        f"{stats_globales['maxima']:.2f}",
        f"{stats_globales['promedio']:.2f}",
    ])

    writer.writerow([])  # línea en blanco

    # Encabezado de detalle por estudiante
    writer.writerow(["DETALLE POR ESTUDIANTE"])
    writer.writerow([
        "ID estudiante",
        "Nombre",
        "RUT",
        "Cantidad notas",
        "Nota mínima",
        "Nota máxima",
        "Promedio",
        "Aprobado",
    ])

    # 5) Detalle por estudiante + actualización de PromedioFinal
    from usuarios.models import User  # import local para evitar dependencias circulares

    for row in promedios_por_estudiante:
        estudiante_id = row["estudiante"]
        promedio = Decimal(str(row["promedio"]))
        minima = Decimal(str(row["minima"]))
        maxima = Decimal(str(row["maxima"]))
        cantidad = row["cantidad"]

        estudiante = User.objects.get(id=estudiante_id)
        aprobado = promedio >= Decimal("4.0")

        # Actualizar/crear PromedioFinal
        PromedioFinal.objects.update_or_create(
            estudiante=estudiante,
            curso=curso,
            asignatura=asignatura,
            periodo=periodo,
            defaults={
                "promedio": promedio,
                "aprobado": aprobado,
            },
        )

        writer.writerow([
            estudiante.id,
            f"{estudiante.first_name} {estudiante.last_name}",
            estudiante.rut or "",
            cantidad,
            f"{minima:.2f}",
            f"{maxima:.2f}",
            f"{promedio:.2f}",
            "Sí" if aprobado else "No",
        ])

    # 6) Guardar CSV en archivo_excel
    csv_content = buffer.getvalue()
    buffer.close()

    file_name = (
        f"reporte_notas_curso{curso.id}_asig{asignatura.id}_periodo{periodo.id}.csv"
    )

    reporte.archivo_excel.save(
        file_name,
        ContentFile(csv_content.encode("utf-8")),
        save=False,
    )
    reporte.save(update_fields=["archivo_excel"])

    return reporte


def generar_reportes_para_periodo(
    periodo: PeriodoAcademico,
    generado_por=None,
) -> None:
    """
    Genera reportes de notas para todos los cursos y asignaturas de un período.

    Esta función es perfecta para ser llamada desde una tarea Celery:
      - mensual
      - al cierre de semestre
    """
    cursos = Curso.objects.filter(periodo=periodo)

    for curso in cursos:
        asignaturas_ids = (
            Calificacion.objects.filter(
                evaluacion__curso=curso,
                evaluacion__periodo=periodo,
            )
            .values_list("evaluacion__asignatura", flat=True)
            .distinct()
        )

        from academico.models import Asignatura as AsigModel

        for asignatura_id in asignaturas_ids:
            asignatura = AsigModel.objects.get(id=asignatura_id)
            generar_reporte_notas_curso_asignatura_periodo(
                curso=curso,
                asignatura=asignatura,
                periodo=periodo,
                generado_por=generado_por,
            )
