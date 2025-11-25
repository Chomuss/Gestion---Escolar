# `Academico` - Gestión de los procesos académicos

## Descripción

La aplicación **`academico`** gestiona todos los aspectos relacionados con el **proceso académico escolar**, incluyendo:

- Asignaturas
- Cursos
- Evaluaciones
- Calificaciones
- Asistencia
- Observaciones académicas y disciplinarias
- Alertas tempranas
- Reportes de notas por periodo
- Reuniones de apoderados

## Funcionalidades

- **Asignaturas**: Crea, edita, elimina y asigna docentes a las asignaturas. Cada asignatura puede estar asociada a uno o más cursos.
- **Cursos**: Gestión de los cursos escolares, asociando a los estudiantes y asignaturas correspondientes.
- **Evaluaciones y Calificaciones**: Registra las evaluaciones (exámenes, pruebas, tareas, etc.) y calificaciones de los estudiantes.
- **Asistencia**: Control de la asistencia de los estudiantes a cada clase, incluyendo la posibilidad de justificar ausencias.
- **Observaciones**: Registra observaciones académicas o disciplinarias para los estudiantes.
- **Alertas Tempranas**: Sistema para detectar y alertar a los apoderados sobre riesgos académicos (bajo rendimiento, muchas ausencias, etc.).
- **Reuniones de Apoderados**: Gestor de reuniones con apoderados para cada curso, para seguir el rendimiento académico y comportamiento de los estudiantes.
- **Reportes de Notas**: Generación de reportes detallados con las calificaciones y el promedio de cada estudiante para un periodo académico específico.

## Herramientas y Tecnologías Utilizadas

- **Django**: Framework web utilizado para el backend.
- **Django REST Framework**: Usado para crear una API RESTful para gestionar los datos académicos de los estudiantes.
- **Celery y Redis**: Para el envío de correos automáticos relacionados con las calificaciones, observaciones, y alertas tempranas.
- **SendGrid**: Para el envío de correos electrónicos con notificaciones automáticas a apoderados y estudiantes.

## Estructura

- **Modelos**: Contiene los modelos de `Curso`, `Asignatura`, `Evaluacion`, `Calificacion`, `Asistencia`, `Observacion`, `AlertaTemprana`, y `ReporteNotasPeriodo`.
- **Serializers**: Define cómo los datos se serializan para ser enviados o recibidos a través de la API.
- **Vistas**: Contiene las vistas de la API para gestionar las asignaturas, cursos, calificaciones, asistencia, y observaciones, además de reportes y alertas.
- **URLs**: Define las rutas de la API para permitir la consulta y manipulación de los datos académicos.
- **Admin**: Configuración de la interfaz de administración de Django para gestionar los procesos académicos.

