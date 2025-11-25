# academico/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    Asistencia,
    Evaluacion,
    Calificacion,
    Observacion,
    EmailQueue,
    AlertaTemprana,
)
from usuarios.models import User


# ============================================================
#  ASISTENCIA
#  - Correo a apoderados cuando se registra asistencia
#  - Alerta temprana por ausencias frecuentes
# ============================================================

@receiver(post_save, sender=Asistencia)
def asistencia_notificacion(sender, instance, created, **kwargs):
    """
    Cuando se registra una nueva asistencia:
    - Se envía correo a los apoderados.
    - Se genera alerta temprana si acumula muchas ausencias.
    """
    if not created:
        return

    estudiante = instance.estudiante

    # Notificar a apoderados del estudiante
    EmailQueue.objects.create(
        tipo_destinatario="APODERADOS",
        destinatario_usuario=estudiante,
        asunto=f"Asistencia registrada para {estudiante.get_full_name()}",
        contenido=(
            f"Estado de asistencia: {instance.estado}\n"
            f"Fecha: {instance.fecha}\n"
            f"Curso: {instance.curso}"
        ),
    )

    # Alerta por ausencias frecuentes
    if instance.estado == "AUSENTE":
        ausencias = Asistencia.objects.filter(
            estudiante=estudiante,
            estado="AUSENTE",
        ).count()

        if ausencias >= 5:
            AlertaTemprana.objects.create(
                estudiante=estudiante,
                curso=instance.curso,
                motivo="Ausencias frecuentes",
                descripcion=f"El estudiante acumula {ausencias} ausencias registradas.",
                nivel="MEDIO",
            )


@receiver(post_save, sender=Asistencia)
def asistencia_justificacion(sender, instance, created, **kwargs):
    """
    Cuando una asistencia cambia a JUSTIFICADO:
    - Se envía correo a apoderados informando la justificación.
    """
    # Solo nos interesa cuando se actualiza (no al crear)
    if created:
        return

    # En el modelo Asistencia usamos 'JUSTIFICADO'
    if instance.estado == "JUSTIFICADO":
        EmailQueue.objects.create(
            tipo_destinatario="APODERADOS",
            destinatario_usuario=instance.estudiante,
            asunto="Asistencia justificada",
            contenido=(
                f"La asistencia del estudiante {instance.estudiante.get_full_name()} "
                f"del día {instance.fecha} ha sido marcada como JUSTIFICADA.\n\n"
                f"Justificación: {instance.justificacion or 'Sin detalle'}"
            ),
        )


# ============================================================
#  EVALUACIONES
#  - Correo al curso cuando se crea una evaluación
# ============================================================

@receiver(post_save, sender=Evaluacion)
def evaluacion_notificacion(sender, instance, created, **kwargs):
    """
    Cuando se crea una nueva evaluación:
    - Se envía correo a todos los estudiantes del curso.
    """
    if not created:
        return

    curso = instance.asignacion.curso
    asignatura = instance.asignacion.asignatura

    EmailQueue.objects.create(
        tipo_destinatario="CURSO",
        destinatario_curso=curso,
        asunto="Nueva evaluación programada",
        contenido=(
            f"Curso: {curso}\n"
            f"Asignatura: {asignatura.nombre}\n"
            f"Título: {instance.titulo}\n"
            f"Tipo: {instance.get_tipo_display()}\n"
            f"Fecha: {instance.fecha.strftime('%d-%m-%Y')}\n"
            f"Ponderación: {instance.ponderacion}%"
        ),
    )


# ============================================================
#  CALIFICACIONES
#  - Correo a apoderados con la nota
#  - Alerta temprana si la nota es baja
# ============================================================

@receiver(post_save, sender=Calificacion)
def calificacion_notificacion(sender, instance, created, **kwargs):
    """
    Cada vez que se registra o actualiza una calificación:
    - Se notifica a los apoderados.
    - Se genera alerta temprana si la nota está bajo el umbral.
    """
    estudiante = instance.estudiante
    evaluacion = instance.evaluacion
    asignatura = evaluacion.asignacion.asignatura
    curso = evaluacion.asignacion.curso

    # Notificar apoderados siempre que haya calificación
    EmailQueue.objects.create(
        tipo_destinatario="APODERADOS",
        destinatario_usuario=estudiante,
        asunto=f"Nueva calificación registrada",
        contenido=(
            f"Estudiante: {estudiante.get_full_name()}\n"
            f"Curso: {curso}\n"
            f"Asignatura: {asignatura.nombre}\n"
            f"Evaluación: {evaluacion.titulo}\n"
            f"Nota: {instance.puntaje_obtenido} / {evaluacion.puntaje_maximo}"
        ),
    )

    # Alerta temprana por nota baja (ejemplo: bajo 60%)
    porcentaje = float(instance.puntaje_obtenido / evaluacion.puntaje_maximo) * 100

    if porcentaje < 60:
        AlertaTemprana.objects.create(
            estudiante=estudiante,
            curso=curso,
            motivo="Calificación insuficiente",
            descripcion=(
                f"Nota baja en {asignatura.nombre}: "
                f"{instance.puntaje_obtenido}/{evaluacion.puntaje_maximo} "
                f"({porcentaje:.1f}%)"
            ),
            nivel="ALTO",
        )


# ============================================================
#  OBSERVACIONES ACADÉMICAS Y DISCIPLINARIAS
#  - Correo a apoderados
#  - Alerta si gravedad es ALTA
# ============================================================

@receiver(post_save, sender=Observacion)
def observacion_notificacion(sender, instance, created, **kwargs):
    """
    Cuando se registra una nueva observación:
    - Se notifica a los apoderados.
    - Se genera alerta si es de gravedad ALTA.
    """
    if not created:
        return

    estudiante = instance.estudiante

    EmailQueue.objects.create(
        tipo_destinatario="APODERADOS",
        destinatario_usuario=estudiante,
        asunto=f"Nueva observación ({instance.get_tipo_display()})",
        contenido=(
            f"Estudiante: {estudiante.get_full_name()}\n"
            f"Curso: {instance.curso or 'Sin curso asociado'}\n"
            f"Tipo: {instance.get_tipo_display()}\n"
            f"Gravedad: {instance.get_gravedad_display()}\n\n"
            f"Descripción:\n{instance.descripcion}"
        ),
    )

    # Si la gravedad es ALTA, registrar alerta temprana
    if instance.gravedad == "ALTA":
        AlertaTemprana.objects.create(
            estudiante=estudiante,
            curso=instance.curso,
            motivo="Observación de alta gravedad",
            descripcion=instance.descripcion,
            nivel="ALTO",
        )


# ============================================================
#  BIENVENIDA A NUEVOS ESTUDIANTES
#  - Correo a apoderados cuando se crea un alumno
# ============================================================

@receiver(post_save, sender=User)
def alumno_bienvenida_apoderados(sender, instance, created, **kwargs):
    """
    Si se crea un usuario con rol ALUMNO:
    - Envía un correo de bienvenida a sus apoderados.
    """
    if not created:
        return

    if not instance.role or instance.role.code != "ALUMNO":
        return

    EmailQueue.objects.create(
        tipo_destinatario="APODERADOS",
        destinatario_usuario=instance,
        asunto="Nuevo estudiante matriculado",
        contenido=(
            f"El estudiante {instance.get_full_name()} ha sido registrado en el sistema "
            f"de gestión escolar.\n\n"
            f"A partir de ahora podrá revisar asistencia, notas, observaciones y "
            f"comunicados oficiales a través de la plataforma."
        ),
    )
