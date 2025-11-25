from celery import shared_task
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils import timezone
from django.db.models import Avg
from django.conf import settings

from .models import (
    EmailQueue,
    AlertaTemprana,
    ReporteNotasPeriodo,
    Calificacion,
    PeriodoAcademico,
)


# ==========================================================================================
#   1. PROCESAR COLA DE CORREOS
# ==========================================================================================

@shared_task(bind=True, max_retries=3)
def procesar_cola_correos(self):
    """
    Envía todos los correos en EmailQueue pendientes.
    Soporta:
        - Usuario individual
        - Curso completo
        - Apoderados del estudiante
    """

    pendientes = EmailQueue.objects.filter(enviado=False)

    for email in pendientes:

        try:
            # Determinar destinatarios
            destinatarios = []

            if email.tipo_destinatario == "USER" and email.destinatario_usuario:
                destinatarios.append(email.destinatario_usuario.email)

            elif email.tipo_destinatario == "CURSO" and email.destinatario_curso:
                matriculados = email.destinatario_curso.matriculas.filter(estado="ACTIVO")
                destinatarios = [m.estudiante.email for m in matriculados if m.estudiante.email]

            elif email.tipo_destinatario == "APODERADOS" and email.destinatario_usuario:
                estudiante = email.destinatario_usuario
                apoderados = estudiante.apoderados.all()
                destinatarios = [a.email for a in apoderados if a.email]

            # No hay destinatarios reales
            if not destinatarios:
                email.enviado = True
                email.enviado_en = timezone.now()
                email.save()
                continue

            # Correo texto o HTML
            if hasattr(email, "contenido_html") and email.contenido_html:
                mensaje = EmailMultiAlternatives(
                    subject=email.asunto,
                    body=email.contenido,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=destinatarios
                )
                mensaje.attach_alternative(email.contenido_html, "text/html")
                mensaje.send()

            else:
                mensaje = EmailMessage(
                    subject=email.asunto,
                    body=email.contenido,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=destinatarios
                )
                mensaje.send()

            # Marcar como enviado
            email.enviado = True
            email.enviado_en = timezone.now()
            email.save()

        except Exception as exc:
            # Reintentar después de 60 segundos
            raise self.retry(exc=exc, countdown=60)

    return "Procesamiento de cola completado"


# ==========================================================================================
#   2. GENERAR ALERTAS TEMPRANAS AUTOMÁTICAS
# ==========================================================================================

@shared_task
def verificar_alertas_tempranas():
    """
    Se ejecuta diariamente.
    Detecta estudiantes en riesgo académico:
        - Promedio general bajo 4.0
        - Múltiples notas bajo 60%
    """

    estudiantes = Calificacion.objects.values_list("estudiante_id", flat=True).distinct()

    for estudiante_id in estudiantes:

        calificaciones = Calificacion.objects.filter(estudiante_id=estudiante_id)

        if not calificaciones.exists():
            continue

        # Promedio general
        promedio = calificaciones.aggregate(avg=Avg("puntaje_obtenido"))["avg"] or 0

        # Conteo de notas deficientes (menor a 60%)
        notas_bajas = sum(
            1 for c in calificaciones
            if (float(c.puntaje_obtenido) / float(c.evaluacion.puntaje_maximo)) * 100 < 60
        )

        curso = calificaciones.first().evaluacion.asignacion.curso

        # Alto riesgo
        if promedio < 4.0 or notas_bajas >= 3:
            AlertaTemprana.objects.create(
                estudiante_id=estudiante_id,
                curso=curso,
                motivo="Rendimiento deficiente",
                descripcion=f"Promedio {promedio:.2f}, notas bajas: {notas_bajas}",
                nivel="ALTO" if promedio < 4.0 else "MEDIO",
            )

    return "Alertas revisadas"


# ==========================================================================================
#   3. GENERACIÓN AUTOMÁTICA DE REPORTES POR PERIODO
# ==========================================================================================

@shared_task
def generar_reporte_periodo():
    """
    Se ejecuta mensualmente.
    Genera el reporte consolidado del estudiante por periodo académico.
    """

    periodos = PeriodoAcademico.objects.all()

    for periodo in periodos:

        estudiantes = Calificacion.objects.filter(
            evaluacion__periodo=periodo
        ).values_list("estudiante_id", flat=True).distinct()

        for estudiante_id in estudiantes:

            promedio = Calificacion.objects.filter(
                estudiante_id=estudiante_id,
                evaluacion__periodo=periodo
            ).aggregate(avg=Avg("puntaje_obtenido"))["avg"] or 0

            ReporteNotasPeriodo.objects.update_or_create(
                estudiante_id=estudiante_id,
                periodo=periodo,
                defaults={"promedio_general": promedio},
            )

    return "Reportes generados"
