from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PeriodoAcademicoViewSet,
    CursoViewSet,
    AsignaturaViewSet,
    SalaViewSet,
    RecursoViewSet,
    BloqueHorarioViewSet,
    HorarioViewSet,
    AsistenciaViewSet,
    EvaluacionViewSet,
    NotaViewSet,
    PromedioFinalViewSet,
    ReunionViewSet,
    ObservacionViewSet,
    IntervencionViewSet,
    AlertaTempranaViewSet,
    ReporteNotasViewSet,
)

router = DefaultRouter()

# Períodos
router.register(r"periodos", PeriodoAcademicoViewSet, basename="periodos")

# Académico base
router.register(r"cursos", CursoViewSet, basename="cursos")
router.register(r"asignaturas", AsignaturaViewSet, basename="asignaturas")
router.register(r"salas", SalaViewSet, basename="salas")
router.register(r"recursos", RecursoViewSet, basename="recursos")

# Horarios
router.register(r"bloques-horarios", BloqueHorarioViewSet, basename="bloques-horarios")
router.register(r"horarios", HorarioViewSet, basename="horarios")

# Asistencia
router.register(r"asistencias", AsistenciaViewSet, basename="asistencias")

# Evaluaciones y notas
router.register(r"evaluaciones", EvaluacionViewSet, basename="evaluaciones")
router.register(r"notas", NotaViewSet, basename="notas")
router.register(r"promedios-finales", PromedioFinalViewSet, basename="promedios-finales")

# Reuniones / convivencia
router.register(r"reuniones", ReunionViewSet, basename="reuniones")
router.register(r"observaciones", ObservacionViewSet, basename="observaciones")
router.register(r"intervenciones", IntervencionViewSet, basename="intervenciones")

# Alertas
router.register(r"alertas-tempranas", AlertaTempranaViewSet, basename="alertas-tempranas")

# Reportes
router.register(r"reportes-notas", ReporteNotasViewSet, basename="reportes-notas")

urlpatterns = [
    path("", include(router.urls)),
]
