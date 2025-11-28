from pathlib import Path

from celery.schedules import crontab

import os
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-!wq6eldrx&jk45nv2ybb2i2ng@cq3%fz$^&w9frm3eiv7^g+^5'
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
    'academico',
    'api',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
]

AUTH_USER_MODEL = 'usuarios.User'


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080", 
    "https://mi-sitio-vue.com", 
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'gestion_escolar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_escolar.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
#  CELERY CONFIG
# ============================================================

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "America/Santiago"
CELERY_ENABLE_UTC = False

# Para tareas periódica

CELERY_BEAT_SCHEDULE = {
    # Detectar alertas tempranas todos los días a las 06:30 AM
    "detectar_alertas_tempranas_diario": {
        "task": "academico.tasks.detectar_alertas_tempranas_task",
        "schedule": crontab(hour=6, minute=30),
    },

    # Controlar atrasos de evaluaciones todos los días a las 08:00 AM
    "controlar_atrasos_evaluaciones_diario": {
        "task": "academico.tasks.controlar_atrasos_evaluaciones_task",
        "schedule": crontab(hour=8, minute=0),
    },

    # Cerrar alertas viejas una vez al día a las 06:00 AM
    "cerrar_alertas_viejas_diario": {
        "task": "academico.tasks.cerrar_alertas_viejas_task",
        "schedule": crontab(hour=6, minute=0),
    },

    # Procesar correos en cola cada 5 minutos
    "procesar_email_queue_cada_5_min": {
        "task": "academico.tasks.procesar_email_queue_task",
        "schedule": crontab(minute="*/5"),
    },
}


# ============================================================
#  CONFIGURACIÓN SMTP PARA SENDGRID
# ============================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "apikey" 
EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = os.getenv("SENDGRID_SENDER")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "api.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
        "DEFAULT_RENDERER_CLASSES": [
        "api.renderers.CustomJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "EXCEPTION_HANDLER": "api.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

}

SPECTACULAR_SETTINGS = {
    "TITLE": "Gestión Escolar API",
    "DESCRIPTION": "API para la gestión académica, usuarios y procesos escolares.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}