from django.urls import path

from .views import (
    # Año académico / periodos
    AnioAcademicoListCreateView,
    AnioAcademicoDetailView,
    PeriodoAcademicoListCreateView,
    PeriodoAcademicoDetailView,

    # Niveles / Cursos
    NivelListCreateView,
    CursoListView,
    CursoCreateView,
    CursoDetailView,

    # Salas
    SalaListCreateView,

    # Asignaturas
    AsignaturaListCreateView,
    AsignaturaDetailView,

    # ACD (Asignatura-Curso-Docente)
    ACDListView,
    ACDCreateView,

    # Matrículas
    MatriculaListView,
    MatriculaCreateView,

    # Horarios
    HorarioListView,
    HorarioCreateView,

    # Asistencia
    AsistenciaCreateView,

    # Evaluaciones
    EvaluacionCreateView,

    # Calificaciones
    CalificacionCreateView,

    # Observaciones
    ObservacionCreateView,

    # Reuniones de apoderados
    ReunionCreateView,

    # Alertas tempranas
    AlertaListView,
    AlertaDetailView,

    # Reporte por periodo
    GenerarReportePeriodo,
)

urlpatterns = [

    # ============================================================
    #  AÑO ACADÉMICO / PERIODOS
    # ============================================================
    path("anio/", AnioAcademicoListCreateView.as_view(), name="anio-list-create"),
    path("anio/<int:pk>/", AnioAcademicoDetailView.as_view(), name="anio-detail"),

    path("periodos/", PeriodoAcademicoListCreateView.as_view(), name="periodo-list-create"),
    path("periodos/<int:pk>/", PeriodoAcademicoDetailView.as_view(), name="periodo-detail"),

    # ============================================================
    #  NIVELES / CURSOS
    # ============================================================
    path("niveles/", NivelListCreateView.as_view(), name="niveles"),
    path("cursos/", CursoListView.as_view(), name="cursos-list"),
    path("cursos/crear/", CursoCreateView.as_view(), name="cursos-create"),
    path("cursos/<int:pk>/", CursoDetailView.as_view(), name="curso-detail"),

    # ============================================================
    #  SALAS
    # ============================================================
    path("salas/", SalaListCreateView.as_view(), name="salas"),

    # ============================================================
    #  ASIGNATURAS
    # ============================================================
    path("asignaturas/", AsignaturaListCreateView.as_view(), name="asignaturas"),
    path("asignaturas/<int:pk>/", AsignaturaDetailView.as_view(), name="asignaturas-detail"),

    # ============================================================
    #  ASIGNATURA – CURSO – DOCENTE (ACD)
    # ============================================================
    path("acd/", ACDListView.as_view(), name="acd-list"),
    path("acd/crear/", ACDCreateView.as_view(), name="acd-create"),

    # ============================================================
    #  MATRÍCULAS
    # ============================================================
    path("matriculas/", MatriculaListView.as_view(), name="matriculas"),
    path("matriculas/crear/", MatriculaCreateView.as_view(), name="matriculas-create"),

    # ============================================================
    #  HORARIOS
    # ============================================================
    path("horarios/", HorarioListView.as_view(), name="horarios"),
    path("horarios/crear/", HorarioCreateView.as_view(), name="horarios-create"),

    # ============================================================
    #  ASISTENCIA
    # ============================================================
    path("asistencia/crear/", AsistenciaCreateView.as_view(), name="asistencia-create"),

    # ============================================================
    #  EVALUACIONES
    # ============================================================
    path("evaluaciones/crear/", EvaluacionCreateView.as_view(), name="evaluaciones-create"),

    # ============================================================
    #  CALIFICACIONES
    # ============================================================
    path("calificaciones/crear/", CalificacionCreateView.as_view(), name="calificaciones-create"),

    # ============================================================
    #  OBSERVACIONES (ACADÉMICAS / DISCIPLINARIAS)
    # ============================================================
    path("observaciones/crear/", ObservacionCreateView.as_view(), name="observaciones-create"),

    # ============================================================
    #  REUNIONES DE APODERADOS
    # ============================================================
    path("reuniones/crear/", ReunionCreateView.as_view(), name="reuniones-create"),

    # ============================================================
    #  ALERTAS TEMPRANAS (RIESGO ACADÉMICO)
    # ============================================================
    path("alertas/", AlertaListView.as_view(), name="alertas"),
    path("alertas/<int:pk>/", AlertaDetailView.as_view(), name="alertas-detail"),

    # ============================================================
    #  REPORTE DE NOTAS POR PERIODO
    # ============================================================
    path("reportes/periodo/", GenerarReportePeriodo.as_view(), name="reporte-periodo"),
]
