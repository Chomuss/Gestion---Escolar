# `API` - Interfaz de Comunicación del Sistema

## Descripción

La aplicación **`api`** es la interfaz de comunicación entre el frontend (Vue.js) y el backend (Django). Gestiona todos los endpoints para consultar y manipular los datos del sistema, permitiendo la integración de las diferentes funcionalidades de las aplicaciones:

- Gestión de usuarios
- Procesos académicos (asistencia, calificaciones, observaciones, etc.)
- Envío de notificaciones y correos
- Reportes académicos

## Funcionalidades

- **Endpoints para el alumno**: Acceso a su dashboard, calificaciones, asistencia, observaciones, y reportes.
- **Endpoints para el docente**: Permite registrar asistencia, calificaciones, observaciones y generar reportes.
- **Endpoints para el apoderado**: Acceso a la información de sus hijos (asistencia, calificaciones, observaciones).
- **Endpoints para el director y administrador**: Panel de control con métricas globales del sistema (número de alumnos, docentes, cursos, alertas).
- **Notificaciones**: Gestión de las notificaciones internas para los usuarios.
- **Correo electrónico**: Envío de notificaciones automáticas de calificaciones, asistencia y alertas.

## Herramientas y Tecnologías Utilizadas

- **Django**: Framework web utilizado para el backend.
- **Django REST Framework**: Usado para crear una API RESTful para gestionar los datos de los usuarios, los procesos académicos y las notificaciones.
- **Celery y Redis**: Para el envío de correos automáticos y tareas en segundo plano.
- **SendGrid**: Para el envío de correos electrónicos.
- **drf-spectacular**: Para generar documentación Swagger/OpenAPI de la API.

## Estructura

- **Modelos**: Define los modelos relacionados con la API, como las calificaciones, asistencia, evaluaciones, y usuarios.
- **Serializers**: Serializa los datos de las entidades para ser enviados a través de la API.
- **Vistas**: Define las vistas de la API para gestionar las consultas de datos.
- **URLs**: Define las rutas de la API para permitir a los usuarios acceder a los diferentes endpoints.
- **Swagger/OpenAPI**: Documentación automática de la API usando `drf-spectacular`.

