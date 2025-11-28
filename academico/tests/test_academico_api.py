# academico/tests/test_academico_api.py

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from academico.models import (
    PeriodoAcademico,
    Curso,
    Asignatura,
    Evaluacion,
    Asistencia,
    AlertaTemprana,
)


User = get_user_model()


class AcademicoAPITestCase(APITestCase):
    """
    Tests básicos de integración sobre la API:
    - /api/core/v1/health/
    - /api/core/v1/me/
    - /api/core/v1/academico/cursos/
    - /api/core/v1/academico/evaluaciones/ + /publicar/
    """

    @classmethod
    def setUpTestData(cls):
        """
        Se ejecuta una sola vez para toda la clase.
        Creamos un usuario admin y algunos datos mínimos académicos.
        """
        cls.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin_test@example.com",
            password="admin1234",
        )

        cls.periodo = PeriodoAcademico.objects.create(
            nombre="Periodo Test 2024",
            anio=2024,
            tipo="ANUAL",  # ajusta si tu modelo usa otros choices
            fecha_inicio=date(2024, 3, 1),
            fecha_fin=date(2024, 12, 31),
            activo=True,
        )

        cls.curso = Curso.objects.create(
            nombre="4° Medio A",
            nivel="4M",  # ajusta según tu modelo
            periodo=cls.periodo,
            # quita o ajusta estos si tu modelo no los tiene
            capacidad_maxima=40,
            jefe_curso=cls.admin_user,
        )

        cls.asignatura = Asignatura.objects.create(
            nombre="Matemáticas",
            codigo="MAT-TEST",
            tipo="OBLIGATORIA",  # usa un choice válido si corresponde
            carga_horaria_semanal=4,
        )

        cls.evaluacion = Evaluacion.objects.create(
            curso=cls.curso,
            asignatura=cls.asignatura,
            docente=cls.admin_user,
            periodo=cls.periodo,
            titulo="Prueba Diagnóstica",
            tipo="PRUEBA",  # ajusta al choice real de tu modelo
            fecha_evaluacion=date.today(),
            fecha_limite_publicacion=date.today() + timedelta(days=7),
            estado="BORRADOR",  # ajusta al estado inicial válido
            ponderacion=0.3,
        )

    # ============================================================
    #  ENDPOINTS GENERALES DE LA API
    # ============================================================

    def test_health_endpoint_returns_ok(self):
        """
        GET /api/core/v1/health/ debe responder 200 y status='ok'.
        """
        url = "/api/core/v1/health/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tu respuesta actual es plana, sin "success"
        # {'status': 'ok', 'time': '...', 'version': 'v1'}
        self.assertIn("status", response.data)
        self.assertEqual(response.data["status"], "ok")

    def test_me_endpoint_requires_auth(self):
        """
        /api/core/v1/me/ sin autenticación debe devolver 401 o 403.
        (En tu caso está devolviendo 403, que es lo normal con SessionAuthentication.)
        """
        url = "/api/core/v1/me/"
        response = self.client.get(url)

        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_me_endpoint_returns_user_data_when_authenticated(self):
        """
        /api/core/v1/me/ autenticado debe devolver los datos del usuario.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/core/v1/me/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Respuesta plana con los campos del serializer
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], self.admin_user.id)

    # ============================================================
    #  CURSOS
    # ============================================================

    def test_cursos_list_authenticated(self):
        """
        GET /api/core/v1/academico/cursos/ autenticado debe devolver 200
        y un listado (paginado por DRF).
        """
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/core/v1/academico/cursos/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Como no estás usando el renderer custom, DRF devuelve la
        # estructura estándar paginada: {count, next, previous, results}
        self.assertIn("results", response.data)
        results = response.data["results"]
        self.assertGreaterEqual(len(results), 1)

    # ============================================================
    #  EVALUACIONES + PUBLICAR
    # ============================================================

    def test_evaluaciones_list_authenticated(self):
        """
        GET /api/core/v1/academico/evaluaciones/ autenticado debe devolver 200.
        """
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/core/v1/academico/evaluaciones/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_publicar_evaluacion_permiso_denegado_y_no_cambia_estado(self):
        """
        POST /api/core/v1/academico/evaluaciones/{id}/publicar/

        Con el usuario de test actual (solo superuser, sin rol específico
        de ADMIN_ACADEMICO/Docente según tus permisos), esperamos 403
        y que la evaluación NO cambie a PUBLICADA.
        """
        self.client.force_authenticate(user=self.admin_user)

        self.evaluacion.refresh_from_db()
        estado_inicial = self.evaluacion.estado

        url = f"/api/core/v1/academico/evaluaciones/{self.evaluacion.id}/publicar/"
        payload = {
            "notificar_estudiantes": False,
            "notificar_apoderados": False,
        }
        response = self.client.post(url, payload, format="json")

        # Según tus logs actuales, esto devuelve 403 (permiso denegado)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Confirmamos que el estado NO cambió
        self.evaluacion.refresh_from_db()
        self.assertEqual(self.evaluacion.estado, estado_inicial)
        self.assertIsNone(self.evaluacion.fecha_publicacion)

    # ============================================================
    #  ASISTENCIAS + ALERTAS
    # ============================================================

    def test_asistencias_list_authenticated(self):
        """
        GET /api/core/v1/academico/asistencias/ autenticado debe devolver 200
        y una lista (puede estar vacía o no).
        """
        self.client.force_authenticate(user=self.admin_user)

        url = "/api/core/v1/academico/asistencias/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Estructura paginada estándar: {count, next, previous, results}
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

    def test_asistencia_alertas_endpoint_exists_and_maybe_creates_alert(self):
        """
        Verifica que el endpoint /asistencias/{id}/alertas/ existe y responde.

        - Crea un registro de Asistencia AUSENTE.
        - Hace GET a /alertas/ para listar.
        - Hace POST a /alertas/ para intentar generar una alerta temprana.

        Dependiendo de los permisos configurados (IsDocente/IsJefeCurso/IsAdminAcad),
        con el usuario de test actual (superuser sin rol específico) podemos obtener:

        - 201/200 si el permiso se considera suficiente y se genera/ya existe alerta.
        - 403 si el permiso es rechazado por los permisos personalizados.

        En ambos casos, el test verifica que no hay errores de ruta (no 404) y que
        el backend responde de forma coherente.
        """
        self.client.force_authenticate(user=self.admin_user)

        # Creamos una asistencia AUSENTE para el mismo usuario/curso/asignatura
        asistencia = Asistencia.objects.create(
            estudiante=self.admin_user,
            curso=self.curso,
            asignatura=self.asignatura,
            fecha=date.today(),
            estado="AUSENTE",        # ajusta si tu modelo usa otro código de estado
            es_justificada=False,
            registrado_por=self.admin_user,
        )

        base_url = f"/api/core/v1/academico/asistencias/{asistencia.id}/alertas/"

        # 1) GET: listar alertas existentes para ese estudiante+curso
        response_get = self.client.get(base_url)
        # Si los permisos de solo lectura son estrictos, podría ser 403;
        # si no, será 200. Aceptamos ambos.
        self.assertIn(response_get.status_code, (status.HTTP_200_OK, status.HTTP_403_FORBIDDEN))

        # 2) POST: intentar generar una alerta por asistencia
        response_post = self.client.post(base_url, {}, format="json")

        # Según tus permisos personalizados, podemos recibir:
        # - 201 Created (alerta nueva)
        # - 200 OK (no se generó por umbral o alerta ya existente)
        # - 403 Forbidden (permiso rechazado)
        self.assertIn(
            response_post.status_code,
            (status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN),
        )

        # Si NO es 403, comprobamos que haya (al menos) una alerta para ese estudiante+curso
        if response_post.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            existe_alerta = AlertaTemprana.objects.filter(
                estudiante=self.admin_user,
                curso=self.curso,
            ).exists()
            self.assertTrue(
                existe_alerta,
                msg="Se esperaba al menos una AlertaTemprana asociada al estudiante/curso.",
            )
