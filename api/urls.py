from django.urls import path

from .views import (
    # Perfil
    MiPerfilAPIView,

    # Alumno
    AlumnoDashboardAPIView,
    AlumnoCursosAPIView,
    AlumnoNotasPorCursoAPIView,
    AlumnoAsistenciaPorCursoAPIView,
    AlumnoObservacionesPorCursoAPIView,
    AlumnoReportePeriodoAPIView,

    # Docente
    DocenteDashboardAPIView,
    DocenteRegistrarAsistenciaAPIView,
    DocenteRegistrarCalificacionAPIView,
    DocenteRegistrarObservacionAPIView,
    DocenteGenerarReportePeriodoAPIView,
    DocenteReportePeriodoAPIView,

    # Apoderado
    ApoderadoDashboardAPIView,

    # Director / Admin
    DirectorDashboardAPIView,
)

urlpatterns = [
    # ========================================================
    #  PERFIL
    # ========================================================
    path("perfil/", MiPerfilAPIView.as_view(), name="api-perfil"),

    # ========================================================
    #  ALUMNO
    # ========================================================
    path(
        "dashboard/alumno/",
        AlumnoDashboardAPIView.as_view(),
        name="api-dashboard-alumno",
    ),
    path(
        "alumno/cursos/",
        AlumnoCursosAPIView.as_view(),
        name="api-alumno-cursos",
    ),
    path(
        "alumno/cursos/<int:curso_id>/notas/",
        AlumnoNotasPorCursoAPIView.as_view(),
        name="api-alumno-notas-curso",
    ),
    path(
        "alumno/cursos/<int:curso_id>/asistencia/",
        AlumnoAsistenciaPorCursoAPIView.as_view(),
        name="api-alumno-asistencia-curso",
    ),
    path(
        "alumno/cursos/<int:curso_id>/observaciones/",
        AlumnoObservacionesPorCursoAPIView.as_view(),
        name="api-alumno-observaciones-curso",
    ),
    path(
        "alumno/cursos/<int:curso_id>/reporte-periodo/<int:periodo_id>/",
        AlumnoReportePeriodoAPIView.as_view(),
        name="api-alumno-reporte-periodo",
    ),

    # ========================================================
    #  DOCENTE
    # ========================================================
    path(
        "dashboard/docente/",
        DocenteDashboardAPIView.as_view(),
        name="api-dashboard-docente",
    ),
    path(
        "docente/asistencia/registrar/",
        DocenteRegistrarAsistenciaAPIView.as_view(),
        name="api-docente-registrar-asistencia",
    ),
    path(
        "docente/calificaciones/registrar/",
        DocenteRegistrarCalificacionAPIView.as_view(),
        name="api-docente-registrar-calificacion",
    ),
    path(
        "docente/observaciones/registrar/",
        DocenteRegistrarObservacionAPIView.as_view(),
        name="api-docente-registrar-observacion",
    ),
    path(
        "docente/reporte-periodo/generar/",
        DocenteGenerarReportePeriodoAPIView.as_view(),
        name="api-docente-generar-reporte-periodo",
    ),
    path(
        "docente/reporte-periodo/<int:periodo_id>/<int:estudiante_id>/",
        DocenteReportePeriodoAPIView.as_view(),
        name="api-docente-reporte-periodo",
    ),

    # ========================================================
    #  APODERADO
    # ========================================================
    path(
        "dashboard/apoderado/",
        ApoderadoDashboardAPIView.as_view(),
        name="api-dashboard-apoderado",
    ),

    # ========================================================
    #  DIRECTOR / ADMIN
    # ========================================================
    path(
        "dashboard/director/",
        DirectorDashboardAPIView.as_view(),
        name="api-dashboard-director",
    ),
]
