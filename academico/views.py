from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg
from django.utils import timezone

from usuarios.views import (
    IsAdminRole, IsDirectorRole, IsDocenteRole, IsAlumnoRole, IsApoderadoRole
)
from usuarios.models import User
from usuarios.serializers import UserSerializer

from .models import (
    AnioAcademico, PeriodoAcademico, Nivel, Curso, Sala, Asignatura,
    AsignaturaCursoDocente, Matricula, BloqueHorario, Asistencia,
    Evaluacion, Calificacion, PromedioFinal, Observacion,
    EmailQueue, ReunionApoderados, AsistenciaReunionApoderado,
    AlertaTemprana, ReporteNotasPeriodo
)

from .serializers import (
    # Año / periodos
    AnioAcademicoSerializer, PeriodoAcademicoSerializer,

    # Nivel / Curso
    NivelSerializer, CursoSerializer, CursoCreateUpdateSerializer,

    # Salas
    SalaSerializer,

    # Asignaturas
    AsignaturaSerializer,

    # Asignación docente
    ACDSerializer, ACDCreateUpdateSerializer,

    # Matrículas
    MatriculaSerializer, MatriculaCreateUpdateSerializer,

    # Horarios
    BloqueHorarioSerializer, BloqueHorarioCreateUpdateSerializer,

    # Asistencia
    AsistenciaSerializer, AsistenciaCreateUpdateSerializer,

    # Evaluaciones
    EvaluacionSerializer, EvaluacionCreateUpdateSerializer,

    # Calificaciones
    CalificacionSerializer, CalificacionCreateUpdateSerializer,

    # Promedio final
    PromedioFinalSerializer, PromedioFinalCreateUpdateSerializer,

    # Observaciones
    ObservacionSerializer, ObservacionCreateUpdateSerializer,

    # EmailQueue
    EmailQueueSerializer, EmailQueueCreateSerializer,

    # Reuniones
    ReunionApoderadosSerializer, ReunionApoderadosCreateUpdateSerializer,
    AsistenciaReunionSerializer, AsistenciaReunionCreateUpdateSerializer,

    # Alertas tempranas
    AlertaTempranaSerializer, AlertaTempranaCreateUpdateSerializer,

    # Reporte periodo
    ReporteNotasPeriodoSerializer, ReporteNotasPeriodoCreateUpdateSerializer,
)

# ============================================================
#  AÑO Y PERIODO ACADEMICO
# ============================================================

class AnioAcademicoListCreateView(generics.ListCreateAPIView):
    queryset = AnioAcademico.objects.all()
    serializer_class = AnioAcademicoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class AnioAcademicoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AnioAcademico.objects.all()
    serializer_class = AnioAcademicoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class PeriodoAcademicoListCreateView(generics.ListCreateAPIView):
    queryset = PeriodoAcademico.objects.select_related("anio").all()
    serializer_class = PeriodoAcademicoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class PeriodoAcademicoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PeriodoAcademico.objects.all()
    serializer_class = PeriodoAcademicoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  NIVEL / CURSOS
# ============================================================

class NivelListCreateView(generics.ListCreateAPIView):
    queryset = Nivel.objects.all()
    serializer_class = NivelSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class CursoListView(generics.ListAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated]


class CursoCreateView(generics.CreateAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class CursoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  SALAS
# ============================================================

class SalaListCreateView(generics.ListCreateAPIView):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  ASIGNATURAS
# ============================================================

class AsignaturaListCreateView(generics.ListCreateAPIView):
    queryset = Asignatura.objects.all()
    serializer_class = AsignaturaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class AsignaturaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Asignatura.objects.all()
    serializer_class = AsignaturaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  ASIGNACION DOCENTE
# ============================================================

class ACDListView(generics.ListAPIView):
    queryset = AsignaturaCursoDocente.objects.all()
    serializer_class = ACDSerializer
    permission_classes = [permissions.IsAuthenticated]


class ACDCreateView(generics.CreateAPIView):
    queryset = AsignaturaCursoDocente.objects.all()
    serializer_class = ACDCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  MATRICULAS
# ============================================================

class MatriculaListView(generics.ListAPIView):
    queryset = Matricula.objects.select_related("estudiante", "curso").all()
    serializer_class = MatriculaSerializer
    permission_classes = [permissions.IsAuthenticated]


class MatriculaCreateView(generics.CreateAPIView):
    queryset = Matricula.objects.all()
    serializer_class = MatriculaCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  HORARIOS
# ============================================================

class HorarioListView(generics.ListAPIView):
    queryset = BloqueHorario.objects.select_related("asignacion").all()
    serializer_class = BloqueHorarioSerializer
    permission_classes = [permissions.IsAuthenticated]


class HorarioCreateView(generics.CreateAPIView):
    queryset = BloqueHorario.objects.all()
    serializer_class = BloqueHorarioCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]



# ============================================================
#  ASISTENCIA
# ============================================================

class AsistenciaCreateView(generics.CreateAPIView):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocenteRole]

    def perform_create(self, serializer):
        asistencia = serializer.save(registrado_por=self.request.user)

        # CORREO AUTOMÁTICO PARA APODERADOS
        EmailQueue.objects.create(
            tipo_destinatario="APODERADOS",
            asunto=f"Asistencia registrada - {asistencia.estudiante}",
            contenido=f"Estado: {asistencia.estado}."
        )

        # ALERTA TEMPRANA SI HAY MUCHAS AUSENCIAS
        ausencias = Asistencia.objects.filter(
            estudiante=asistencia.estudiante,
            estado="AUSENTE"
        ).count()

        if ausencias >= 5:
            AlertaTemprana.objects.create(
                estudiante=asistencia.estudiante,
                curso=asistencia.curso,
                motivo="Altas ausencias",
                descripcion="Se detectaron múltiples ausencias consecutivas.",
                nivel="MEDIO",
                generada_por=self.request.user,
            )



# ============================================================
#  EVALUACIONES
# ============================================================

class EvaluacionCreateView(generics.CreateAPIView):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocenteRole]

    def perform_create(self, serializer):
        evaluacion = serializer.save(creado_por=self.request.user)

        # CORREO AUTOMÁTICO A TODO EL CURSO
        EmailQueue.objects.create(
            tipo_destinatario="CURSO",
            destinatario_curso=evaluacion.asignacion.curso,
            asunto="Nueva evaluación programada",
            contenido=f"Evaluación: {evaluacion.titulo}\nFecha: {evaluacion.fecha}",
        )



# ============================================================
#  NOTAS
# ============================================================

class CalificacionCreateView(generics.CreateAPIView):
    queryset = Calificacion.objects.all()
    serializer_class = CalificacionCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocenteRole]

    def perform_create(self, serializer):
        calificacion = serializer.save(registrado_por=self.request.user)

        # CORREO A APODERADOS
        EmailQueue.objects.create(
            tipo_destinatario="APODERADOS",
            asunto=f"Calificación registrada en {calificacion.evaluacion.asignacion.asignatura.nombre}",
            contenido=f"Nota: {calificacion.puntaje_obtenido}/{calificacion.evaluacion.puntaje_maximo}",
        )

        # ALERTA TEMPRANA SI LA NOTA ES BAJA
        porcentaje = float(calificacion.puntaje_obtenido / calificacion.evaluacion.puntaje_maximo) * 100
        if porcentaje < 60:
            AlertaTemprana.objects.create(
                estudiante=calificacion.estudiante,
                curso=calificacion.evaluacion.asignacion.curso,
                motivo="Bajo rendimiento",
                descripcion=f"Nota baja: {calificacion.puntaje_obtenido}",
                nivel="ALTO",
                generada_por=self.request.user
            )



# ============================================================
#  OBSERVACIONES
# ============================================================

class ObservacionCreateView(generics.CreateAPIView):
    queryset = Observacion.objects.all()
    serializer_class = ObservacionCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocenteRole]

    def perform_create(self, serializer):
        observacion = serializer.save(registrada_por=self.request.user)

        # CORREO AUTOMÁTICO
        EmailQueue.objects.create(
            tipo_destinatario="APODERADOS",
            asunto=f"Nueva observación registrada",
            contenido=f"Tipo: {observacion.tipo}\nGravedad: {observacion.gravedad}\n{observacion.descripcion}",
        )



# ============================================================
#  REUNIONES DE APODERADOS
# ============================================================

class ReunionCreateView(generics.CreateAPIView):
    queryset = ReunionApoderados.objects.all()
    serializer_class = ReunionApoderadosCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocenteRole]

    def perform_create(self, serializer):
        reunion = serializer.save(docente=self.request.user)

        # Avisar correos a todo el curso
        EmailQueue.objects.create(
            tipo_destinatario="CURSO",
            destinatario_curso=reunion.curso,
            asunto="Reunión de apoderados",
            contenido=f"Fecha: {reunion.fecha}\nTema: {reunion.tema}",
        )



# ============================================================
#  ALERTAS TEMPRANAS
# ============================================================

class AlertaListView(generics.ListAPIView):
    queryset = AlertaTemprana.objects.all()
    serializer_class = AlertaTempranaSerializer
    permission_classes = [permissions.IsAuthenticated, IsDirectorRole]


class AlertaDetailView(generics.RetrieveAPIView):
    queryset = AlertaTemprana.objects.all()
    serializer_class = AlertaTempranaSerializer
    permission_classes = [permissions.IsAuthenticated, IsDirectorRole]



# ============================================================
#  REPORTE DE NOTAS POR PERIODO
# ============================================================

class GenerarReportePeriodo(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDocenteRole]

    def post(self, request):
        estudiante_id = request.data.get("estudiante_id")
        periodo_id = request.data.get("periodo_id")

        estudiante = User.objects.get(id=estudiante_id)
        periodo = PeriodoAcademico.objects.get(id=periodo_id)

        promedio = Calificacion.objects.filter(
            estudiante=estudiante,
            evaluacion__periodo=periodo
        ).aggregate(avg=Avg("puntaje_obtenido"))["avg"] or 0

        reporte = ReporteNotasPeriodo.objects.create(
            estudiante=estudiante,
            periodo=periodo,
            promedio_general=promedio,
        )

        return Response(ReporteNotasPeriodoSerializer(reporte).data)
