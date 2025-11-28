from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import (
    Asistencia,
    Calificacion,
    Evaluacion,
    AlertaTemprana,
    Curso,
    PeriodoAcademico,
    EmailQueue,
)
from usuarios.models import Notification

# Servicios de dominio
from academico.services import asistencia as asistencia_service
from academico.services import alerta as alerta_service
from academico.services import reporte as reporte_service
from academico.services import evaluacion as evaluacion_service

User = get_user_model()

# -------------------------------------------------------------------
#  PARÁMETROS DE NEGOCIO 
# -------------------------------------------------------------------

# % de inasistencia sobre el total de clases en un rango que dispara alerta (solo para filtro rápido)
ALERTA_INASISTENCIA_PORCENTAJE = 20

# Nota bajo este umbral se considera crítica
UMBRAL_NOTA_BAJA = 4.0

# Mínimo de evaluaciones para considerar el promedio como “confiable”
MIN_EVALUACIONES_PARA_ALERTA = 3

# Días después de la fecha límite para marcar una evaluación como atrasada
DIAS_ATRASO_EVALUACION = 1

# Días sin movimiento para cerrar alertas antiguas
DIAS_CIERRE_ALERTA = 60


# ============================================================
# 1) DETECTAR ALERTAS TEMPRANAS (ASISTENCIA + NOTAS)
# ============================================================

@shared_task
def detectar_alertas_tempranas_task():
    """
    Detecta alertas tempranas por:
      - Asistencia (alto ausentismo)
      - Notas bajas

    Usa:
      - servicios de asistencia (para ausentismo)
      - servicios de alerta (para creación y notificación)
    """

    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)

    # ------------------------------------------------------------------
    # 1. ALERTAS POR ASISTENCIA (usa asistencia_service + alerta_service)
    # ------------------------------------------------------------------
    # Tomamos combinaciones estudiante-curso que tengan registros de asistencia
    pares = (
        Asistencia.objects.filter(fecha__range=(hace_30_dias, hoy))
        .values("estudiante", "curso")
        .distinct()
    )

    for par in pares:
        estudiante_id = par["estudiante"]
        curso_id = par["curso"]

        if not estudiante_id or not curso_id:
            continue

        try:
            estudiante = User.objects.get(id=estudiante_id)
            curso = Curso.objects.get(id=curso_id)
        except (User.DoesNotExist, Curso.DoesNotExist):
            continue

        asistencia_service.generar_alerta_por_asistencia(
            estudiante=estudiante,
            curso=curso,
            periodo=getattr(curso, "periodo", None),
            porcentaje_umbral=ALERTA_INASISTENCIA_PORCENTAJE,
            ventana_dias=30,
            creada_por=None, 
        )

    # ------------------------------------------------------------------
    # 2. ALERTAS POR NOTAS BAJAS (usa alerta_service)
    # ------------------------------------------------------------------
    # Calculamos promedios por estudiante/curso/asignatura
    notas_qs = (
        Calificacion.objects.values("estudiante", "evaluacion__curso", "evaluacion__asignatura")
        .annotate(
            promedio=Avg("nota"),
            cantidad=Count("id"),
        )
        .filter(cantidad__gte=MIN_EVALUACIONES_PARA_ALERTA)
        .filter(promedio__lt=UMBRAL_NOTA_BAJA)
    )

    from academico.models import Asignatura  

    for registro in notas_qs:
        estudiante_id = registro["estudiante"]
        curso_id = registro["evaluacion__curso"]
        asignatura_id = registro["evaluacion__asignatura"]
        promedio = float(registro["promedio"])

        try:
            estudiante = User.objects.get(id=estudiante_id)
            curso = Curso.objects.get(id=curso_id)
            asignatura = Asignatura.objects.get(id=asignatura_id)
        except (User.DoesNotExist, Curso.DoesNotExist, Asignatura.DoesNotExist):
            continue

        descripcion = (
            f"Promedio {promedio:.1f} inferior al umbral {UMBRAL_NOTA_BAJA:.1f} "
            f"en la asignatura {asignatura}."
        )

        nivel_riesgo = "ALTO" if promedio < 3.0 else "MEDIO"

        alerta_service.crear_alerta_temprana_automatizada(
            estudiante=estudiante,
            curso=curso,
            asignatura=asignatura,
            origen="NOTAS", 
            descripcion=descripcion,
            nivel_riesgo=nivel_riesgo,
            creada_por=None,
            ventana_dias_sin_duplicar=15,
        )


# ============================================================
# 2) GENERAR REPORTES DE NOTAS POR PERÍODO
# ============================================================

@shared_task
def generar_reportes_notas_periodo_task(periodo_id=None, generado_por_id=None):
    """
    Genera reportes de notas (ReporteNotasPeriodo) para todos los cursos y
    asignaturas de un período determinado.

    Delega la lógica de negocio a:
      - academico.services.reporte.generar_reportes_para_periodo
    """
    if periodo_id is None:
        periodo = PeriodoAcademico.objects.filter(activo=True).first()
    else:
        periodo = PeriodoAcademico.objects.filter(id=periodo_id).first()

    if not periodo:
        return

    generado_por = None
    if generado_por_id is not None:
        try:
            generado_por = User.objects.get(id=generado_por_id)
        except User.DoesNotExist:
            generado_por = None

    reporte_service.generar_reportes_para_periodo(
        periodo=periodo,
        generado_por=generado_por,
    )


# ============================================================
# 3) PROCESAR COLA DE CORREOS
# ============================================================

@shared_task
def procesar_email_queue_task(max_emails=50):
    """
    Toma hasta 'max_emails' correos en estado PENDIENTE y los envía
    usando la configuración de correo de Django.
    Marca como ENVIADO o FALLIDO según corresponda.
    """
    pendientes = EmailQueue.objects.filter(estado="PENDIENTE")[:max_emails]

    for email in pendientes:
        try:
            send_mail(
                subject=email.asunto,
                message=email.cuerpo,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email.destinatario],
                fail_silently=False,
            )
            email.estado = "ENVIADO"  
            email.ultimo_error = ""
        except Exception as e:
            email.estado = "FALLIDO"
            email.ultimo_error = str(e)[:500]
        email.save(update_fields=["estado", "ultimo_error"])


# ============================================================
# 4) CONTROLAR ATRASOS DE EVALUACIONES
# ============================================================

@shared_task
def controlar_atrasos_evaluaciones_task():
    """
    Marca evaluaciones como 'ATRASADA' si:
      - ya pasó la fecha_limite_publicacion + DIAS_ATRASO_EVALUACION
      - todavía no están PUBLICADAS

    Delega el cambio de estado a:
      - evaluacion_service.actualizar_estado_por_atraso

    Y si la evaluación pasa a ATRASADA, notifica al docente.
    """
    ahora = timezone.now()
    hoy = ahora.date()
    limite_atraso = hoy - timedelta(days=DIAS_ATRASO_EVALUACION)

    evaluaciones = Evaluacion.objects.filter(
        fecha_limite_publicacion__lte=limite_atraso,
    ).exclude(estado="PUBLICADA")

    for evaluacion in evaluaciones:
        estado_anterior = evaluacion.estado

        evaluacion_service.actualizar_estado_por_atraso(
            evaluacion=evaluacion,
            referencia_fecha=ahora,
        )

        if estado_anterior != "ATRASADA" and evaluacion.estado == "ATRASADA":
            _notificar_evaluacion_atrasada(evaluacion)


def _notificar_evaluacion_atrasada(evaluacion: Evaluacion) -> None:
    """
    Notifica al docente responsable que la evaluación se marcó como ATRASADA
    y encola un correo (si tiene email).
    """
    docente = evaluacion.docente
    curso = evaluacion.curso

    if not docente:
        return

    Notification.objects.create(
        user=docente,
        title="Evaluación atrasada",
        message=(
            f"La evaluación '{evaluacion.titulo}' del curso {curso.nombre} "
            f"ha excedido la fecha límite de publicación "
            f"({evaluacion.fecha_limite_publicacion})."
        ),
        level="WARN",
    )

    if docente.email:
        EmailQueue.objects.create(
            destinatario=docente.email,
            asunto="Evaluación atrasada",
            cuerpo=(
                f"Estimado(a) {docente.first_name},\n\n"
                f"La evaluación \"{evaluacion.titulo}\" del curso {curso.nombre} "
                f"ha excedido la fecha límite de publicación "
                f"({evaluacion.fecha_limite_publicacion}).\n"
            ),
        )


# ============================================================
# 5) CERRAR ALERTAS VIEJAS
# ============================================================

@shared_task
def cerrar_alertas_viejas_task():
    """
    Cambia a 'CERRADA' las alertas tempranas muy antiguas
    que sigan en estado 'ABIERTA'.

    Delega el cierre concreto a:
      - alerta_service.cerrar_alerta
    """
    ahora = timezone.now()
    limite_antiguedad = ahora - timedelta(days=DIAS_CIERRE_ALERTA)

    alertas = AlertaTemprana.objects.filter(
        estado="ABIERTA",
        fecha_creacion__lte=limite_antiguedad,
    )

    for alerta in alertas:
        alerta_service.cerrar_alerta(alerta, usuario=None)
