from datetime import date
from typing import Optional, Dict

from django.db.models import Count, Q
from django.utils import timezone

from academico.models import Asistencia, Curso, PeriodoAcademico, AlertaTemprana, EmailQueue
from usuarios.models import Notification, User

from . import alerta as alerta_service


def calcular_ausentismo_estudiante(
    estudiante: User,
    curso: Optional[Curso] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> Dict[str, float]:
    """
    Calcula estadísticas de asistencia/ausentismo para un estudiante
    en un rango de fechas opcional y, opcionalmente, para un curso.

    Retorna un dict con:
      - total_registros
      - total_ausencias (AUSENTE + JUSTIFICADO)
      - total_atrasos
      - porcentaje_ausencia
      - porcentaje_atraso
    """
    qs = Asistencia.objects.filter(estudiante=estudiante)

    if curso:
        qs = qs.filter(curso=curso)

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    stats = qs.aggregate(
        total=Count("id"),
        ausencias=Count("id", filter=Q(estado__in=["AUSENTE", "JUSTIFICADO"])),
        atrasos=Count("id", filter=Q(estado="ATRASO")),
    )

    total = stats["total"] or 0
    ausencias = stats["ausencias"] or 0
    atrasos = stats["atrasos"] or 0

    if total == 0:
        return {
            "total_registros": 0,
            "total_ausencias": 0,
            "total_atrasos": 0,
            "porcentaje_ausencia": 0.0,
            "porcentaje_atraso": 0.0,
        }

    porcentaje_ausencia = (ausencias * 100.0) / total
    porcentaje_atraso = (atrasos * 100.0) / total

    return {
        "total_registros": total,
        "total_ausencias": ausencias,
        "total_atrasos": atrasos,
        "porcentaje_ausencia": porcentaje_ausencia,
        "porcentaje_atraso": porcentaje_atraso,
    }


def generar_alerta_por_asistencia(
    estudiante: User,
    curso: Curso,
    periodo: Optional[PeriodoAcademico] = None,
    porcentaje_umbral: float = 20.0,
    ventana_dias: int = 30,
    creada_por: Optional[User] = None,
) -> Optional[AlertaTemprana]:
    """
    Genera una alerta temprana de tipo ASISTENCIA para un estudiante
    si su porcentaje de inasistencia en la ventana de días indicada
    supera el umbral.

    Usa el servicio alerta.crear_alerta_temprana_automatizada para
    evitar duplicados recientes.
    """
    hoy = timezone.now().date()
    fecha_desde = hoy - timezone.timedelta(days=ventana_dias)

    stats = calcular_ausentismo_estudiante(
        estudiante=estudiante,
        curso=curso,
        fecha_desde=fecha_desde,
        fecha_hasta=hoy,
    )

    if stats["total_registros"] == 0:
        return None

    if stats["porcentaje_ausencia"] < porcentaje_umbral:
        return None

    descripcion = (
        f"Inasistencia de {stats['porcentaje_ausencia']:.1f}% "
        f"en los últimos {ventana_dias} días "
        f"({stats['total_ausencias']} ausencias de {stats['total_registros']} registros)."
    )

    alerta = alerta_service.crear_alerta_temprana_automatizada(
        estudiante=estudiante,
        curso=curso,
        asignatura=None,
        origen="ASISTENCIA",
        descripcion=descripcion,
        nivel_riesgo="ALTO" if stats["porcentaje_ausencia"] >= 30 else "MEDIO",
        creada_por=creada_por,
        ventana_dias_sin_duplicar=15,
    )

    return alerta


def notificar_apoderados_por_inasistencia(asistencia: Asistencia) -> None:
    """
    Envía notificaciones y correos a los apoderados del estudiante
    cuando hay una inasistencia (AUSENTE o JUSTIFICADO) o un atraso.

    Usa la relación:
      - alumno.apoderados (ManyToMany hacia User)
    """
    estudiante: User = asistencia.estudiante
    curso: Curso = asistencia.curso
    apoderados = estudiante.apoderados.all()

    if not apoderados.exists():
        return

    # Mensaje base
    if asistencia.estado == "AUSENTE":
        asunto_base = "Inasistencia a clase"
        estado_legible = "ausente"
    elif asistencia.estado == "JUSTIFICADO":
        asunto_base = "Inasistencia justificada"
        estado_legible = "ausente (justificado)"
    elif asistencia.estado == "ATRASO":
        asunto_base = "Atraso a clase"
        estado_legible = "atrasado"
    else:
        # Si está presente, no notifica
        return

    for apoderado in apoderados:
        # Notificación interna
        Notification.objects.create(
            user=apoderado,
            title=asunto_base,
            message=(
                f"El estudiante {estudiante.first_name} {estudiante.last_name} "
                f"del curso {curso.nombre} ha estado {estado_legible} el día "
                f"{asistencia.fecha}."
            ),
            level="INFO",
        )

        # Email en cola
        if apoderado.email:
            cuerpo = (
                f"Estimado(a) {apoderado.first_name},\n\n"
                f"Le informamos que el estudiante {estudiante.first_name} {estudiante.last_name} "
                f"del curso {curso.nombre} ha estado {estado_legible} el día {asistencia.fecha}.\n"
            )
            if asistencia.motivo_inasistencia:
                cuerpo += f"\nMotivo registrado: {asistencia.motivo_inasistencia}\n"

            EmailQueue.objects.create(
                destinatario=apoderado.email,
                asunto=asunto_base,
                cuerpo=cuerpo,
            )
