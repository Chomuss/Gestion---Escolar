from datetime import timedelta
from typing import Optional

from django.utils import timezone

from academico.models import AlertaTemprana, Curso, Asignatura, EmailQueue
from usuarios.models import User, Notification


def crear_alerta_temprana_automatizada(
    estudiante: User,
    curso: Curso,
    asignatura: Optional[Asignatura],
    origen: str,
    descripcion: str,
    nivel_riesgo: str = "MEDIO",
    creada_por: Optional[User] = None,
    ventana_dias_sin_duplicar: int = 15,
) -> Optional[AlertaTemprana]:
    """
    Crea una alerta temprana evitando duplicados recientes.

    No crea la alerta si ya existe una alerta ABIERTA del mismo:
      - estudiante
      - curso
      - asignatura (puede ser None)
      - origen
    en los últimos `ventana_dias_sin_duplicar` días.
    """
    ahora = timezone.now()
    limite = ahora - timedelta(days=ventana_dias_sin_duplicar)

    existe = AlertaTemprana.objects.filter(
        estudiante=estudiante,
        curso=curso,
        asignatura=asignatura,
        origen=origen,
        estado="ABIERTA",
        fecha_creacion__gte=limite,
    ).exists()

    if existe:
        return None

    alerta = AlertaTemprana.objects.create(
        estudiante=estudiante,
        curso=curso,
        asignatura=asignatura,
        origen=origen,
        descripcion=descripcion,
        nivel_riesgo=nivel_riesgo,
        estado="ABIERTA",
        creada_por=creada_por,
    )

    enviar_notificaciones_alerta(alerta)
    return alerta


def enviar_notificaciones_alerta(alerta: AlertaTemprana) -> None:
    """
    Envía notificaciones internas y correos en cola relacionados con una alerta.
    Por defecto, notifica al jefe de curso (si existe).
    """
    estudiante = alerta.estudiante
    curso = alerta.curso
    jefe_curso = curso.jefe_curso if curso else None

    # nivel de notificación
    nivel_riesgo = alerta.nivel_riesgo
    if nivel_riesgo == "ALTO":
        level = "URGENT"
    elif nivel_riesgo == "MEDIO":
        level = "WARN"
    else:
        level = "INFO"

    if jefe_curso:
        Notification.objects.create(
            user=jefe_curso,
            title="Nueva alerta temprana",
            message=(
                f"Se ha generado una alerta temprana ({alerta.origen}) para el estudiante "
                f"{estudiante.first_name} {estudiante.last_name} "
                f"del curso {curso.nombre}.\n\n"
                f"Nivel de riesgo: {alerta.nivel_riesgo}\n"
                f"Descripción: {alerta.descripcion}"
            ),
            level=level,
        )

        if jefe_curso.email:
            EmailQueue.objects.create(
                destinatario=jefe_curso.email,
                asunto="Nueva alerta temprana de estudiante",
                cuerpo=(
                    f"Estimado(a) {jefe_curso.first_name},\n\n"
                    f"Se ha generado una alerta temprana ({alerta.origen}) para el estudiante "
                    f"{estudiante.first_name} {estudiante.last_name} "
                    f"del curso {curso.nombre}.\n\n"
                    f"Nivel de riesgo: {alerta.nivel_riesgo}\n"
                    f"Descripción: {alerta.descripcion}\n"
                ),
            )


def cerrar_alerta(
    alerta: AlertaTemprana,
    usuario: Optional[User] = None,
) -> AlertaTemprana:
    """
    Cierra una alerta temprana, fijando fecha_cierre y estado=CERRADA.
    """
    if alerta.estado == "CERRADA":
        return alerta

    ahora = timezone.now()
    alerta.estado = "CERRADA"
    alerta.fecha_cierre = ahora
    alerta.save(update_fields=["estado", "fecha_cierre"])

    # Notificación al responsable
    if usuario:
        Notification.objects.create(
            user=usuario,
            title="Alerta cerrada",
            message=f"La alerta temprana para {alerta.estudiante} ha sido cerrada.",
            level="INFO",
        )

    return alerta
