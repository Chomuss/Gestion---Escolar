# `Gestión Escolar` - Sistema Completo para Gestión Académica

## Descripción

El proyecto **`gestión escolar`** es una aplicación integral que permite gestionar el ciclo académico en una institución educativa. Incluye el manejo de usuarios (estudiantes, docentes, apoderados), registros académicos (calificaciones, asistencia), generación de reportes, y envío de notificaciones.

## Funcionalidades

- **Gestión de usuarios**: Manejo de roles, permisos y grupos institucionales.
- **Gestión académica**: Gestión de cursos, asignaturas, evaluaciones, calificaciones, asistencia y observaciones.
- **Notificaciones y comunicaciones**: Envío de notificaciones automáticas a los usuarios a través de correos electrónicos.


## Herramientas y Tecnologías Utilizadas

- **Django**: Framework principal para el backend.
- **Django REST Framework**: Para la creación de la API RESTful.
- **Celery y Redis**: Para el manejo de tareas en segundo plano, como el envío de correos.
- **SendGrid**: Para el envío de correos electrónicos.
- **drf-spectacular**: Para la documentación automática de la API (Swagger/OpenAPI).

## Estructura

- **Aplicación `usuarios`**: Gestiona todo lo relacionado con los usuarios, roles, permisos y autenticación.
- **Aplicación `academico`**: Gestiona el ciclo académico (cursos, asignaturas, calificaciones, asistencia).
- **Aplicación `api`**: Expone la API RESTful para interactuar con el frontend y otros servicios.
- **Aplicación `gestion_escolar`**: La raíz del proyecto, que incluye la configuración general y las aplicaciones anteriores.
