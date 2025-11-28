# academico/services/evaluacion.py

from decimal import Decimal
from typing import Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from academico.models import (
    Evaluacion,
    Calificacion,
    PromedioFinal,
    Curso,
    Asignatura,
    PeriodoAcademico,
    EmailQueue,
)
from usuarios.models import Notification, User


def validar_fechas_evaluacion(evaluacion: Evaluacion) -> None:
    """
    Valida coherencia de fechas de una evaluación:
      - fecha_limite_publicacion >= fecha_evaluacion
      - fecha_publicacion (si existe) no puede ser anterior a fecha_evaluacion
    Lanza ValidationError si hay errores.
    """
    errores = {}

    if evaluacion.fecha_limite_publicacion and evaluacion.fecha_evaluacion:
        if evaluacion.fecha_limite_publicacion < evaluacion.fecha_evaluacion:
            errores["fecha_limite_publicacion"] = (
                "La fecha límite de publicación no puede ser anterior "
                "a la fecha de evaluación."
            )

    if evaluacion.fecha_publicacion and evaluacion.fecha_evaluacion:
        if evaluacion.fecha_publicacion.date() < evaluacion.fecha_evaluacion:
            errores["fecha_publicacion"] = (
                "La fecha de publicación no puede ser anterior "
                "a la fecha de evaluación."
            )

    if errores:
        raise ValidationError(errores)


def actualizar_estado_por_atraso(
    evaluacion: Evaluacion,
    referencia_fecha: Optional[timezone.datetime] = None,
) -> None:
    """
    Actualiza el estado de una evaluación a ATRASADA si:
      - No está PUBLICADA
      - La fecha_limite_publicacion ya pasó (según referencia_fecha o ahora)
    Guarda solo si hay cambios.
    """
    if evaluacion.estado == "PUBLICADA":
        return

    if not evaluacion.fecha_limite_publicacion:
        return

    ref = referencia_fecha or timezone.now()
    if evaluacion.fecha_limite_publicacion < ref.date() and evaluacion.estado != "ATRASADA":
        evaluacion.estado = "ATRASADA"
        evaluacion.save(update_fields=["estado"])


@transaction.atomic
def publicar_evaluacion(
    evaluacion: Evaluacion,
    usuario: Optional[User] = None,
    notificar_estudiantes: bool = True,
    notificar_apoderados: bool = False,
) -> Evaluacion:
    """
    Marca una evaluación como PUBLICADA, fija fecha_publicacion (ahora) y
    opcionalmente envía notificaciones a estudiantes (y apoderados).

    Se ejecuta dentro de una transacción atómica.
    """
    if evaluacion.estado == "PUBLICADA":
        return evaluacion

    validar_fechas_evaluacion(evaluacion)

    evaluacion.estado = "PUBLICADA"
    evaluacion.fecha_publicacion = timezone.now()
    evaluacion.save(update_fields=["estado", "fecha_publicacion"])

    curso: Curso = evaluacion.curso
    asignatura: Asignatura = evaluacion.asignatura

    estudiantes = curso.estudiantes.all()

    # Notificación interna a docentes o usuario que publica
    destinatario_docente = usuario or evaluacion.docente
    if destinatario_docente:
        Notification.objects.create(
            user=destinatario_docente,
            title="Evaluación publicada",
            message=(
                f"La evaluación '{evaluacion.titulo}' para el curso {curso.nombre} "
                f"y asignatura {asignatura.nombre if asignatura else ''} ha sido publicada."
            ),
            level="INFO",
        )

    # Notificaciones a estudiantes
    if notificar_estudiantes:
        for est in estudiantes:
            Notification.objects.create(
                user=est,
                title="Nueva evaluación publicada",
                message=(
                    f"Se han publicado las notas de la evaluación '{evaluacion.titulo}' "
                    f"del curso {curso.nombre}."
                ),
                level="INFO",
            )

    # Correos a apoderados -> usamos relación alumno.apoderados
    if notificar_apoderados:
        for est in estudiantes:
            for apoderado in est.apoderados.all():
                if not apoderado.email:
                    continue
                EmailQueue.objects.create(
                    destinatario=apoderado.email,
                    asunto="Evaluación publicada",
                    cuerpo=(
                        f"Estimado(a) {apoderado.first_name},\n\n"
                        f"Le informamos que se han publicado las notas de la evaluación "
                        f"'{evaluacion.titulo}' del curso {curso.nombre} para el estudiante "
                        f"{est.first_name} {est.last_name}.\n"
                    ),
                )

    return evaluacion


def calcular_promedio_estudiante_curso_asignatura_periodo(
    estudiante: User,
    curso: Curso,
    asignatura: Asignatura,
    periodo: PeriodoAcademico,
) -> Optional[Decimal]:
    """
    Calcula el promedio de notas de un estudiante para un curso + asignatura + período.

    Considera todas las Calificaciones cuya Evaluación coincida con:
      - curso
      - asignatura
      - periodo
    Retorna un Decimal con el promedio o None si no hay calificaciones.
    """
    qs = Calificacion.objects.filter(
        estudiante=estudiante,
        evaluacion__curso=curso,
        evaluacion__asignatura=asignatura,
        evaluacion__periodo=periodo,
    )

    if not qs.exists():
        return None

    result = qs.aggregate(promedio=Avg("nota"))
    promedio = result["promedio"]

    return Decimal(str(promedio)) if promedio is not None else None


@transaction.atomic
def recalcular_promedios_finales_curso_asignatura(
    curso: Curso,
    asignatura: Asignatura,
    periodo: PeriodoAcademico,
    aprobar_desde: Decimal = Decimal("4.0"),
) -> None:
    """
    Recalcula/crea PromedioFinal para todos los estudiantes de un curso
    y asignatura en un período dado.

    - crea o actualiza PromedioFinal
    - marca aprobado=True si promedio >= aprobar_desde
    """
    estudiantes = curso.estudiantes.all()

    for estudiante in estudiantes:
        promedio = calcular_promedio_estudiante_curso_asignatura_periodo(
            estudiante=estudiante,
            curso=curso,
            asignatura=asignatura,
            periodo=periodo,
        )

        if promedio is None:
            continue

        aprobado = promedio >= aprobar_desde

        obj, _created = PromedioFinal.objects.update_or_create(
            estudiante=estudiante,
            curso=curso,
            asignatura=asignatura,
            periodo=periodo,
            defaults={
                "promedio": promedio,
                "aprobado": aprobado,
            },
        )
