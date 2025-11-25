# `Usuarios` - Gestión de los usuarios del sistema

## Descripción

La aplicación **`usuarios`** se encarga de gestionar los usuarios dentro del sistema, incluyendo:

- Roles (Administrador, Docente, Alumno, Apoderado)
- Permisos y grupos
- Información personal y de cuenta
- Seguridad (bloqueo de cuentas, intentos fallidos, etc.)
- Auditoría y logs de actividad
- Configuración de perfiles de usuario

## Funcionalidades

- **Roles**: Gestión de los roles de los usuarios (Administrador, Docente, Alumno, Apoderado).
- **Permisos**: Definición de permisos adicionales específicos de la institución (por ejemplo, "ver_asistencia", "registrar_notas").
- **Grupos Institucionales**: Gestión de los grupos a los que los usuarios pueden pertenecer, tales como cursos, niveles, o talleres.
- **Usuario Personalizado**: Extiende el modelo de usuario de Django (`AbstractUser`) para incluir campos como `rut`, `phone`, `address`, `profile_image` y relaciones con apoderados.
- **Seguridad**: Implementación de bloqueo de cuentas, gestión de intentos fallidos y contraseñas.
- **Auditoría**: Registro de acciones administrativas y log de actividad de los usuarios.
- **Notificaciones**: Sistema de notificaciones internas para comunicar cambios importantes a los usuarios.

## Herramientas y Tecnologías Utilizadas

- **Django**: Framework web utilizado para el backend.
- **Django REST Framework**: Usado para crear una API RESTful que gestiona los usuarios.
- **Django Admin**: Interfaz de administración para gestionar los usuarios, roles y permisos.
- **Celery y Redis**: Para la gestión de tareas en segundo plano, como el envío de notificaciones.

## Estructura

- **Modelos**: Define el modelo `User` personalizado, roles, permisos, grupos y logs de actividad.
- **Serializers**: Serializa los datos de los usuarios para la API.
- **Vistas**: Vistas que permiten a los administradores gestionar los usuarios, roles, permisos y notificaciones.
- **URLs**: Define las rutas de la API para gestionar usuarios, roles y permisos.
- **Admin**: Configuración de la interfaz de administración de Django para la gestión de usuarios y roles.

