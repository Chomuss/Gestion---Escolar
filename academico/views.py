from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework import filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response

from django.contrib.auth import get_user_model

from .models import (
    PeriodoAcademico,
    Curso,
    Asignatura,
    Sala,
    Recurso,
    BloqueHorario,
    HorarioCurso,
    Asistencia,
    Evaluacion,
    Calificacion,
    PromedioFinal,
    Observacion,
    AlertaTemprana,
    Intervencion,
    ReunionApoderados,
    ReporteNotasPeriodo,
)
from .serializers import (
    PeriodoAcademicoSerializer,
    CursoSerializer,
    AsignaturaSerializer,
    SalaSerializer,
    RecursoSerializer,
    BloqueHorarioSerializer,
    HorarioCursoSerializer,
    AsistenciaSerializer,
    EvaluacionSerializer,
    CalificacionSerializer,
    PromedioFinalSerializer,
    ObservacionSerializer,
    AlertaTempranaSerializer,
    IntervencionSerializer,
    ReunionApoderadosSerializer,
    ReporteNotasPeriodoSerializer,
    UsuarioSimpleSerializer,
)
from .filters import (
    CursoFilter,
    AsignaturaFilter,
    AsistenciaFilter,
    PromedioFinalFilter,
    AlertaTempranaFilter,
    EvaluacionFilter,
)
from .permissions import (
    IsAdministradorAcademico,
    IsDocenteOrAdministradorAcademico,
    IsDocenteOrJefeCursoOrAdministradorAcademico,
)

# Services
from academico.services import (
    asistencia as asistencia_service,
    evaluacion as evaluacion_service,
    alerta as alerta_service,
)

# Utils
from academico.utils import excel as excel_utils
from academico.utils import pdf as pdf_utils

User = get_user_model()


# ============================================================
#  BASE VIEWSET
# ============================================================

class BaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet base con configuración común:
    - Autenticación obligatoria
    - Filtros: django-filter, búsqueda y ordenamiento
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]


# ============================================================
#  PERÍODOS ACADÉMICOS
# ============================================================

class PeriodoAcademicoViewSet(BaseViewSet):
    queryset = PeriodoAcademico.objects.all()
    serializer_class = PeriodoAcademicoSerializer
    search_fields = ["nombre", "anio", "tipo"]
    ordering_fields = ["anio", "fecha_inicio", "fecha_fin"]
    ordering = ["-anio", "-fecha_inicio"]

    def get_permissions(self):
        # Solo admin académico puede crear/editar periodos; otros solo leen
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  CURSOS
# ============================================================

class CursoViewSet(BaseViewSet):
    queryset = (
        Curso.objects
        .select_related("periodo", "jefe_curso")
        .prefetch_related("estudiantes")
        .all()
    )
    serializer_class = CursoSerializer
    filterset_class = CursoFilter
    search_fields = ["nombre", "nivel", "periodo__nombre"]
    ordering_fields = ["nivel", "nombre", "periodo__anio"]
    ordering = ["nivel", "nombre"]

    def get_permissions(self):
        # Crear/editar/eliminar cursos
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdministradorAcademico()]
        # Listar/ver cursos 
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["get"], url_path="horario")
    def horario(self, request, pk=None):
        """
        /cursos/{id}/horario/
        Devuelve el horario completo del curso (HorariosCurso).
        """
        curso = self.get_object()
        qs = (
            HorarioCurso.objects
            .select_related("curso", "asignatura", "docente", "sala", "bloque", "periodo")
            .filter(curso=curso)
        )
        serializer = HorarioCursoSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="estudiantes")
    def estudiantes(self, request, pk=None):
        """
        /cursos/{id}/estudiantes/
        Devuelve la lista de estudiantes del curso.
        """
        curso = self.get_object()
        estudiantes = curso.estudiantes.all()
        serializer = UsuarioSimpleSerializer(estudiantes, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


# ============================================================
#  ASIGNATURAS
# ============================================================

class AsignaturaViewSet(BaseViewSet):
    queryset = Asignatura.objects.all()
    serializer_class = AsignaturaSerializer
    filterset_class = AsignaturaFilter
    search_fields = ["nombre", "codigo"]
    ordering_fields = ["nombre", "codigo"]
    ordering = ["nombre"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  SALAS
# ============================================================

class SalaViewSet(BaseViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    search_fields = ["nombre", "codigo"]
    ordering_fields = ["nombre", "codigo", "capacidad"]
    ordering = ["nombre"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  RECURSOS
# ============================================================

class RecursoViewSet(BaseViewSet):
    queryset = Recurso.objects.select_related("sala").all()
    serializer_class = RecursoSerializer
    search_fields = ["nombre", "sala__nombre"]
    ordering_fields = ["nombre"]
    ordering = ["nombre"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  BLOQUES Y HORARIOS DE CURSO
# ============================================================

class BloqueHorarioViewSet(BaseViewSet):
    queryset = BloqueHorario.objects.select_related("periodo").all()
    serializer_class = BloqueHorarioSerializer
    search_fields = ["periodo__nombre"]
    ordering_fields = ["dia_semana", "hora_inicio", "hora_fin"]
    ordering = ["dia_semana", "hora_inicio"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Docente o Admin académico
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


class HorarioViewSet(BaseViewSet):
    """
    Horarios de curso (HorariosCurso).
    """
    queryset = (
        HorarioCurso.objects
        .select_related("curso", "asignatura", "docente", "sala", "bloque", "periodo")
        .all()
    )
    serializer_class = HorarioCursoSerializer
    search_fields = ["curso__nombre", "asignatura__nombre", "docente__last_name"]
    ordering_fields = ["curso__nombre", "bloque__dia_semana", "bloque__hora_inicio"]
    ordering = ["curso__nombre", "bloque__dia_semana", "bloque__hora_inicio"]

    def get_permissions(self):
        # Crear/editar/eliminar horarios
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  ASISTENCIA
# ============================================================

class AsistenciaViewSet(BaseViewSet):
    queryset = (
        Asistencia.objects
        .select_related("estudiante", "curso", "asignatura", "registrado_por")
        .all()
    )
    serializer_class = AsistenciaSerializer
    filterset_class = AsistenciaFilter
    search_fields = ["estudiante__first_name", "estudiante__last_name", "curso__nombre"]
    ordering_fields = ["fecha", "curso__nombre", "asignatura__nombre"]
    ordering = ["-fecha"]

    def get_permissions(self):
        # Registrar/modificar asistencia 
        if self.action in ["create", "update", "partial_update", "destroy", "alertas"]:
            return [permissions.IsAuthenticated(), IsDocenteOrJefeCursoOrAdministradorAcademico()]
        # Ver asistencia
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["get", "post"], url_path="alertas")
    def alertas(self, request, pk=None):
        """
        /asistencias/{id}/alertas/

        GET:
          - Lista alertas tempranas relacionadas al estudiante+curso de esta asistencia.

        POST:
          - Dispara el flujo de generación de alerta por asistencia
            (si cumple criterios de ausentismo) y devuelve la alerta creada
            o un mensaje indicando que no se generó.
        """
        asistencia = self.get_object()
        estudiante = asistencia.estudiante
        curso = asistencia.curso

        if request.method == "GET":
            qs = AlertaTemprana.objects.filter(estudiante=estudiante, curso=curso)
            serializer = AlertaTempranaSerializer(qs, many=True, context=self.get_serializer_context())
            return Response(serializer.data)

        alerta = asistencia_service.generar_alerta_por_asistencia(
            estudiante=estudiante,
            curso=curso,
            periodo=getattr(curso, "periodo", None),
            porcentaje_umbral=20.0,
            ventana_dias=30,
            creada_por=request.user,
        )

        if not alerta:
            return Response(
                {"detail": "No se generó una nueva alerta (no se superó el umbral o ya existe una alerta abierta reciente)."},
                status=status.HTTP_200_OK,
            )

        serializer = AlertaTempranaSerializer(alerta, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================================
#  EVALUACIONES
# ============================================================

class EvaluacionViewSet(BaseViewSet):
    queryset = (
        Evaluacion.objects
        .select_related("curso", "asignatura", "docente", "periodo")
        .all()
    )
    serializer_class = EvaluacionSerializer
    filterset_class = EvaluacionFilter
    search_fields = ["titulo", "descripcion", "curso__nombre", "asignatura__nombre"]
    ordering_fields = ["fecha_evaluacion", "fecha_limite_publicacion", "estado", "tipo"]
    ordering = ["-fecha_evaluacion"]

    def get_permissions(self):
        # Crear/modificar evaluaciones
        if self.action in ["create", "update", "partial_update", "destroy", "publicar", "exportar_notas_excel"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        # Ver evaluaciones 
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="publicar")
    def publicar(self, request, pk=None):
        """
        /evaluaciones/{id}/publicar/

        Publica una evaluación:
          - Cambia estado a PUBLICADA
          - Fija fecha_publicacion
          - Opcionalmente notifica a estudiantes y apoderados

        Body JSON (opcional):
        {
          "notificar_estudiantes": true/false,
          "notificar_apoderados": true/false
        }
        """
        evaluacion = self.get_object()

        def _parse_bool(value, default=False):
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            return str(value).lower() in ["1", "true", "t", "yes", "on"]

        notificar_estudiantes = _parse_bool(request.data.get("notificar_estudiantes"), default=True)
        notificar_apoderados = _parse_bool(request.data.get("notificar_apoderados"), default=False)

        evaluacion = evaluacion_service.publicar_evaluacion(
            evaluacion=evaluacion,
            usuario=request.user,
            notificar_estudiantes=notificar_estudiantes,
            notificar_apoderados=notificar_apoderados,
        )

        serializer = self.get_serializer(evaluacion)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="exportar-notas-excel")
    def exportar_notas_excel(self, request, pk=None):
        """
        /evaluaciones/{id}/exportar-notas-excel/

        Devuelve un CSV (compatible con Excel) con las notas de la evaluación.
        """
        evaluacion = self.get_object()
        csv_content = excel_utils.generar_csv_notas_evaluacion(evaluacion)
        file_name = f"notas_evaluacion_{evaluacion.id}.csv"

        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response


# ============================================================
#  NOTAS
# ============================================================

class NotaViewSet(BaseViewSet):
    """
    Gestiona Calificaciones (notas).
    """
    queryset = (
        Calificacion.objects
        .select_related("evaluacion", "estudiante", "evaluacion__curso", "evaluacion__asignatura")
        .all()
    )
    serializer_class = CalificacionSerializer
    search_fields = ["estudiante__first_name", "estudiante__last_name", "evaluacion__titulo"]
    ordering_fields = ["nota", "fecha_registro"]
    ordering = ["-fecha_registro"]

    def get_permissions(self):
        # Crear/modificar notas
        if self.action in ["create", "update", "partial_update", "destroy", "importar_excel"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        # Ver notas
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["post"], url_path="importar-excel")
    def importar_excel(self, request):
        """
        /notas/importar-excel/

        Importa notas desde un archivo CSV (Excel) para una evaluación.

        Espera:
        - evaluacion: ID de la evaluación
        - archivo: archivo CSV subido (multipart/form-data)

        Retorna:
        {
          "evaluacion": <id>,
          "procesados": <int>
        }
        """
        evaluacion_id = request.data.get("evaluacion")
        archivo = request.FILES.get("archivo")

        if not evaluacion_id or not archivo:
            return Response(
                {"detail": "Debe enviar 'evaluacion' y el archivo en 'archivo'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            evaluacion = Evaluacion.objects.select_related("docente").get(id=evaluacion_id)
        except Evaluacion.DoesNotExist:
            return Response(
                {"detail": "La evaluación indicada no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Seguridad extra: solo el docente de la evaluación o admin académico
        user = request.user
        es_docente_eval = evaluacion.docente_id == user.id
        es_admin_academico = getattr(user, "role", None) and user.role.code in ["ADMIN", "DIRECTOR"]

        if not (es_docente_eval or es_admin_academico):
            return Response(
                {"detail": "No tiene permisos para importar notas en esta evaluación."},
                status=status.HTTP_403_FORBIDDEN,
            )

        procesados = excel_utils.importar_notas_desde_csv_para_evaluacion(
            evaluacion=evaluacion,
            file=archivo,
            actualizar_existentes=True,
        )

        return Response(
            {"evaluacion": evaluacion.id, "procesados": procesados},
            status=status.HTTP_200_OK,
        )


# ============================================================
#  PROMEDIOS FINALES
# ============================================================

class PromedioFinalViewSet(BaseViewSet):
    queryset = (
        PromedioFinal.objects
        .select_related("estudiante", "curso", "asignatura", "periodo")
        .all()
    )
    serializer_class = PromedioFinalSerializer
    filterset_class = PromedioFinalFilter
    search_fields = ["estudiante__first_name", "estudiante__last_name", "curso__nombre"]
    ordering_fields = ["promedio", "fecha_calculo"]
    ordering = ["-fecha_calculo"]

    def get_permissions(self):
        # Lectura: todos; modificación: solo admin académico
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  REUNIONES CON APODERADOS
# ============================================================

class ReunionViewSet(BaseViewSet):
    """
    Gestiona reuniones con apoderados (ReunionApoderados).
    """
    queryset = (
        ReunionApoderados.objects
        .select_related("curso", "estudiante", "apoderado", "docente")
        .all()
    )
    serializer_class = ReunionApoderadosSerializer
    search_fields = ["curso__nombre", "estudiante__last_name", "apoderado__last_name"]
    ordering_fields = ["fecha", "curso__nombre"]
    ordering = ["-fecha"]

    def get_permissions(self):
        # Crear/editar reuniones
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  OBSERVACIONES
# ============================================================

class ObservacionViewSet(BaseViewSet):
    queryset = (
        Observacion.objects
        .select_related("estudiante", "autor", "curso")
        .all()
    )
    serializer_class = ObservacionSerializer
    search_fields = [
        "estudiante__first_name",
        "estudiante__last_name",
        "curso__nombre",
        "descripcion",
    ]
    ordering_fields = ["fecha", "gravedad"]
    ordering = ["-fecha"]

    def get_permissions(self):
        # Crear/editar observaciones
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  INTERVENCIONES
# ============================================================

class IntervencionViewSet(BaseViewSet):
    queryset = (
        Intervencion.objects
        .select_related("estudiante", "alerta", "observacion", "responsable")
        .all()
    )
    serializer_class = IntervencionSerializer
    search_fields = [
        "estudiante__first_name",
        "estudiante__last_name",
        "responsable__last_name",
        "descripcion",
    ]
    ordering_fields = ["fecha", "estado"]
    ordering = ["-fecha"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        return [permissions.IsAuthenticated()]


# ============================================================
#  ALERTAS TEMPRANAS
# ============================================================

class AlertaTempranaViewSet(BaseViewSet):
    queryset = (
        AlertaTemprana.objects
        .select_related("estudiante", "curso", "creada_por")
        .all()
    )
    serializer_class = AlertaTempranaSerializer
    filterset_class = AlertaTempranaFilter
    search_fields = [
        "estudiante__first_name",
        "estudiante__last_name",
        "curso__nombre",
        "descripcion",
    ]
    ordering_fields = ["fecha_creacion", "nivel_riesgo", "estado"]
    ordering = ["-fecha_creacion"]

    def get_permissions(self):
        # Cerrar o crear alertas
        if self.action in ["create", "update", "partial_update", "destroy", "cerrar"]:
            return [permissions.IsAuthenticated(), IsDocenteOrAdministradorAcademico()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        """
        /alertas-tempranas/{id}/cerrar/

        Marca una alerta como CERRADA.
        """
        alerta = self.get_object()
        alerta = alerta_service.cerrar_alerta(alerta, usuario=request.user)
        serializer = self.get_serializer(alerta)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
#  REPORTES DE NOTAS POR PERÍODO
# ============================================================

class ReporteNotasViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Reportes de notas por período (ReporteNotasPeriodo).

    Normalmente se generan vía Celery/servicio, pero aquí se exponen
    para consulta, y se agrega una acción para generar PDF.
    """
    queryset = (
        ReporteNotasPeriodo.objects
        .select_related("curso", "asignatura", "periodo", "generado_por")
        .all()
    )
    serializer_class = ReporteNotasPeriodoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ["curso__nombre", "asignatura__nombre", "periodo__nombre"]
    ordering_fields = ["fecha_generacion", "curso__nombre", "asignatura__nombre"]
    ordering = ["-fecha_generacion"]

    @action(detail=True, methods=["post"], url_path="generar-pdf")
    def generar_pdf(self, request, pk=None):
        """
        /reportes-notas/{id}/generar-pdf/

        Genera (o regenera) el PDF asociado a este reporte
        y lo guarda en el campo archivo_pdf.
        """
        reporte = self.get_object()
        pdf_utils.adjuntar_pdf_a_reporte(reporte)
        serializer = self.get_serializer(reporte)
        return Response(serializer.data, status=status.HTTP_200_OK)
