from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)

from usuarios.models import User
from academico.models import (
    Curso,
    Matricula,
    Asistencia,
    Calificacion,
    Observacion,
    Evaluacion,
    AlertaTemprana,
    ReporteNotasPeriodo,
)

from .serializers import (
    UsuarioSerializer,
    CursoSerializer,
    AsistenciaSerializer,
    CalificacionSerializer,
    ObservacionSerializer,
    EvaluacionSerializer,
    AlertaTempranaSerializer,
    ReportePeriodoSerializer,
)
from academico.serializers import (
    AsistenciaCreateUpdateSerializer,
    CalificacionCreateUpdateSerializer,
    ObservacionCreateUpdateSerializer,
)

from .permissions import (
    IsAlumno,
    IsDocente,
    IsApoderado,
    IsAdmin,
    IsDirector,
)


# ============================================================
#  PERFIL
# ============================================================

@extend_schema(
    summary="Obtener mi perfil",
    description="Devuelve los datos del usuario autenticado, incluyendo su rol.",
    responses={200: UsuarioSerializer},
)
class MiPerfilAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


# ============================================================
#  ALUMNO – DASHBOARD GENERAL
# ============================================================

@extend_schema(
    summary="Dashboard general del alumno",
    description=(
        "Devuelve calificaciones, asistencias, observaciones y alertas del alumno autenticado."
    ),
    responses={
        200: OpenApiResponse(
            description="Datos generales del alumno (notas, asistencia, observaciones, alertas)."
        )
    },
)
class AlumnoDashboardAPIView(APIView):
    permission_classes = [IsAlumno]

    def get(self, request):
        alumno = request.user

        calificaciones = Calificacion.objects.filter(estudiante=alumno)
        asistencias = Asistencia.objects.filter(estudiante=alumno)
        observaciones = Observacion.objects.filter(estudiante=alumno)
        alertas = AlertaTemprana.objects.filter(estudiante=alumno)

        data = {
            "calificaciones": CalificacionSerializer(calificaciones, many=True).data,
            "asistencias": AsistenciaSerializer(asistencias, many=True).data,
            "observaciones": ObservacionSerializer(observaciones, many=True).data,
            "alertas": AlertaTempranaSerializer(alertas, many=True).data,
        }
        return Response(data)


# ============================================================
#  ALUMNO – CURSOS
# ============================================================

@extend_schema(
    summary="Listar cursos del alumno",
    description="Retorna los cursos en los que el alumno está matriculado con estado ACTIVO.",
    responses={200: CursoSerializer(many=True)},
)
class AlumnoCursosAPIView(APIView):
    permission_classes = [IsAlumno]

    def get(self, request):
        alumno = request.user
        matriculas = Matricula.objects.select_related(
            "curso", "curso__nivel", "anio_academico"
        ).filter(
            estudiante=alumno,
            estado="ACTIVO",
        )
        cursos = [m.curso for m in matriculas]
        return Response(CursoSerializer(cursos, many=True).data)


# ============================================================
#  ALUMNO – NOTAS / ASISTENCIA / OBSERVACIONES POR CURSO
# ============================================================

@extend_schema(
    summary="Notas del alumno en un curso",
    description="Devuelve todas las calificaciones del alumno en el curso indicado.",
    parameters=[
        OpenApiParameter(
            name="curso_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del curso",
        ),
    ],
    responses={200: CalificacionSerializer(many=True)},
)
class AlumnoNotasPorCursoAPIView(APIView):
    permission_classes = [IsAlumno]

    def get(self, request, curso_id):
        alumno = request.user

        calificaciones = Calificacion.objects.select_related(
            "evaluacion",
            "evaluacion__asignacion",
            "evaluacion__asignacion__asignatura",
            "evaluacion__asignacion__curso",
        ).filter(
            estudiante=alumno,
            evaluacion__asignacion__curso_id=curso_id,
        )

        return Response(CalificacionSerializer(calificaciones, many=True).data)


@extend_schema(
    summary="Asistencia del alumno en un curso",
    description="Devuelve los registros de asistencia del alumno para el curso indicado.",
    parameters=[
        OpenApiParameter(
            name="curso_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del curso",
        ),
    ],
    responses={200: AsistenciaSerializer(many=True)},
)
class AlumnoAsistenciaPorCursoAPIView(APIView):
    permission_classes = [IsAlumno]

    def get(self, request, curso_id):
        alumno = request.user

        asistencias = Asistencia.objects.select_related(
            "asignatura",
            "curso",
        ).filter(
            estudiante=alumno,
            curso_id=curso_id,
        )

        return Response(AsistenciaSerializer(asistencias, many=True).data)


@extend_schema(
    summary="Observaciones del alumno en un curso",
    description="Devuelve observaciones académicas y disciplinarias del alumno para el curso indicado.",
    parameters=[
        OpenApiParameter(
            name="curso_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del curso",
        ),
    ],
    responses={200: ObservacionSerializer(many=True)},
)
class AlumnoObservacionesPorCursoAPIView(APIView):
    permission_classes = [IsAlumno]

    def get(self, request, curso_id):
        alumno = request.user

        observaciones = Observacion.objects.select_related(
            "curso",
        ).filter(
            estudiante=alumno,
            curso_id=curso_id,
        )

        return Response(ObservacionSerializer(observaciones, many=True).data)


# ============================================================
#  ALUMNO – REPORTE DE NOTAS POR PERIODO
# ============================================================

@extend_schema(
    summary="Reporte académico del alumno por periodo",
    description=(
        "Devuelve el reporte consolidado del alumno para un periodo y curso: "
        "reporte general, calificaciones y evaluaciones."
    ),
    parameters=[
        OpenApiParameter(
            name="curso_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del curso",
        ),
        OpenApiParameter(
            name="periodo_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del periodo académico",
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Reporte del periodo con resumen, calificaciones y evaluaciones."
        ),
        400: OpenApiResponse(description="Alumno no pertenece al curso."),
        404: OpenApiResponse(description="No existe reporte para ese periodo."),
    },
)
class AlumnoReportePeriodoAPIView(APIView):
    permission_classes = [IsAlumno]

    def get(self, request, curso_id, periodo_id):
        alumno = request.user

        # Validar matrícula
        if not Matricula.objects.filter(
            estudiante=alumno,
            curso_id=curso_id,
            estado="ACTIVO"
        ).exists():
            return Response(
                {"detail": "No estás matriculado en este curso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reporte = ReporteNotasPeriodo.objects.filter(
            estudiante=alumno,
            periodo_id=periodo_id,
        ).first()

        if not reporte:
            return Response(
                {"detail": "Aún no existe un reporte para este periodo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        calificaciones = Calificacion.objects.filter(
            estudiante=alumno,
            evaluacion__periodo_id=periodo_id,
            evaluacion__asignacion__curso_id=curso_id,
        )

        evaluaciones = Evaluacion.objects.filter(
            periodo_id=periodo_id,
            asignacion__curso_id=curso_id,
        )

        data = {
            "reporte": ReportePeriodoSerializer(reporte).data,
            "calificaciones": CalificacionSerializer(calificaciones, many=True).data,
            "evaluaciones": EvaluacionSerializer(evaluaciones, many=True).data,
        }

        return Response(data)

# ============================================================
#  DOCENTE – DASHBOARD GENERAL
# ============================================================

@extend_schema(
    summary="Dashboard general del docente",
    description=(
        "Devuelve cursos donde hace clases, evaluaciones creadas y observaciones registradas por el docente."
    ),
    responses={
        200: OpenApiResponse(
            description="Cursos, evaluaciones y observaciones del docente."
        )
    },
)
class DocenteDashboardAPIView(APIView):
    permission_classes = [IsDocente]

    def get(self, request):
        docente = request.user

        cursos = Curso.objects.filter(
            asignaturas_curso__docente=docente
        ).distinct()

        evaluaciones = Evaluacion.objects.filter(creado_por=docente)
        observaciones = Observacion.objects.filter(registrada_por=docente)

        data = {
            "cursos": CursoSerializer(cursos, many=True).data,
            "evaluaciones": EvaluacionSerializer(evaluaciones, many=True).data,
            "observaciones": ObservacionSerializer(observaciones, many=True).data,
        }
        return Response(data)


# ============================================================
#  DOCENTE – REGISTRO DE ASISTENCIA
# ============================================================

@extend_schema(
    summary="Registrar asistencia",
    description=(
        "Permite al docente registrar la asistencia de un estudiante en una asignatura y curso."
    ),
    request=AsistenciaCreateUpdateSerializer,
    responses={
        201: AsistenciaSerializer,
        400: OpenApiResponse(description="Datos inválidos."),
    },
)
class DocenteRegistrarAsistenciaAPIView(APIView):
    permission_classes = [IsDocente]

    def post(self, request):
        serializer = AsistenciaCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            instancia = serializer.save(registrado_por=request.user)
            return Response(
                AsistenciaSerializer(instancia).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
#  DOCENTE – REGISTRO DE CALIFICACIONES
# ============================================================

@extend_schema(
    summary="Registrar calificación",
    description="Permite al docente registrar la nota de un estudiante en una evaluación.",
    request=CalificacionCreateUpdateSerializer,
    responses={
        201: CalificacionSerializer,
        400: OpenApiResponse(description="Datos inválidos."),
    },
)
class DocenteRegistrarCalificacionAPIView(APIView):
    permission_classes = [IsDocente]

    def post(self, request):
        serializer = CalificacionCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            instancia = serializer.save(registrado_por=request.user)
            return Response(
                CalificacionSerializer(instancia).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
#  DOCENTE – REGISTRO DE OBSERVACIONES
# ============================================================

@extend_schema(
    summary="Registrar observación",
    description=(
        "Permite al docente registrar una observación académica o disciplinaria para un estudiante."
    ),
    request=ObservacionCreateUpdateSerializer,
    responses={
        201: ObservacionSerializer,
        400: OpenApiResponse(description="Datos inválidos."),
    },
)
class DocenteRegistrarObservacionAPIView(APIView):
    permission_classes = [IsDocente]

    def post(self, request):
        serializer = ObservacionCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            instancia = serializer.save(registrada_por=request.user)
            return Response(
                ObservacionSerializer(instancia).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
#  DOCENTE – GENERAR / CONSULTAR REPORTE POR PERIODO
# ============================================================

@extend_schema(
    summary="Generar reporte de notas por periodo",
    description="Genera o actualiza el reporte de notas de un estudiante para un periodo académico.",
    request={
        "type": "object",
        "properties": {
            "estudiante": {"type": "integer", "description": "ID del estudiante"},
            "periodo": {"type": "integer", "description": "ID del periodo académico"},
        },
        "required": ["estudiante", "periodo"],
    },
    responses={
        200: ReportePeriodoSerializer,
        201: ReportePeriodoSerializer,
        400: OpenApiResponse(description="Datos inválidos."),
        404: OpenApiResponse(description="No hay calificaciones para el periodo."),
    },
)
class DocenteGenerarReportePeriodoAPIView(APIView):
    permission_classes = [IsDocente]

    def post(self, request):
        estudiante_id = request.data.get("estudiante")
        periodo_id = request.data.get("periodo")

        if not estudiante_id or not periodo_id:
            return Response(
                {"detail": "Debe enviar estudiante y periodo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            estudiante = User.objects.get(id=estudiante_id, role__code="ALUMNO")
        except User.DoesNotExist:
            return Response(
                {"detail": "Estudiante no válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calificaciones = Calificacion.objects.filter(
            estudiante_id=estudiante_id,
            evaluacion__periodo_id=periodo_id,
        )

        if not calificaciones.exists():
            return Response(
                {"detail": "No hay calificaciones en este periodo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        promedio_general = sum(c.puntaje_obtenido for c in calificaciones) / calificaciones.count()

        reporte, created = ReporteNotasPeriodo.objects.update_or_create(
            estudiante=estudiante,
            periodo_id=periodo_id,
            defaults={"promedio_general": promedio_general},
        )

        return Response(
            ReportePeriodoSerializer(reporte).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(
    summary="Consultar reporte de notas por periodo (docente)",
    description="Permite al docente consultar el reporte de un estudiante para un periodo.",
    parameters=[
        OpenApiParameter(
            name="periodo_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del periodo académico",
        ),
        OpenApiParameter(
            name="estudiante_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID del estudiante",
        ),
    ],
    responses={
        200: ReportePeriodoSerializer,
        404: OpenApiResponse(description="Reporte no encontrado."),
    },
)
class DocenteReportePeriodoAPIView(APIView):
    permission_classes = [IsDocente]

    def get(self, request, periodo_id, estudiante_id):
        try:
            reporte = ReporteNotasPeriodo.objects.get(
                estudiante_id=estudiante_id,
                periodo_id=periodo_id,
            )
        except ReporteNotasPeriodo.DoesNotExist:
            return Response(
                {"detail": "Reporte no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ReportePeriodoSerializer(reporte).data)


# ============================================================
#  APODERADO – DASHBOARD
# ============================================================

@extend_schema(
    summary="Dashboard del apoderado",
    description="Devuelve información académica de todos los estudiantes asociados al apoderado.",
    responses={
        200: OpenApiResponse(
            description="Listado de estudiantes con sus notas, asistencias, observaciones y alertas."
        )
    },
)
class ApoderadoDashboardAPIView(APIView):
    permission_classes = [IsApoderado]

    def get(self, request):
        apoderado = request.user
        estudiantes = apoderado.hijos.all()  # relación definida en usuarios

        resultado = []

        for estudiante in estudiantes:
            data = {
                "estudiante": UsuarioSerializer(estudiante).data,
                "asistencias": AsistenciaSerializer(
                    Asistencia.objects.filter(estudiante=estudiante), many=True
                ).data,
                "calificaciones": CalificacionSerializer(
                    Calificacion.objects.filter(estudiante=estudiante), many=True
                ).data,
                "observaciones": ObservacionSerializer(
                    Observacion.objects.filter(estudiante=estudiante), many=True
                ).data,
                "alertas": AlertaTempranaSerializer(
                    AlertaTemprana.objects.filter(estudiante=estudiante), many=True
                ).data,
            }
            resultado.append(data)

        return Response(resultado)


# ============================================================
#  DIRECTOR / ADMIN – PANEL GENERAL
# ============================================================

@extend_schema(
    summary="Dashboard de director/administrador",
    description="Métricas globales del establecimiento (alumnos, docentes, cursos, alertas).",
    responses={
        200: OpenApiResponse(
            description="Totales de alumnos, docentes, cursos y alertas tempranas."
        )
    },
)
class DirectorDashboardAPIView(APIView):
    permission_classes = [IsDirector | IsAdmin]

    def get(self, request):
        data = {
            "total_alumnos": User.objects.filter(role__code="ALUMNO").count(),
            "total_docentes": User.objects.filter(role__code="DOCENTE").count(),
            "total_cursos": Curso.objects.count(),
            "total_alertas": AlertaTemprana.objects.count(),
        }
        return Response(data)
