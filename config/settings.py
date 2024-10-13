import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-cc08ms-44e13y9*ti!^ugp7z4_t3)0#44h4hw5egd(wlzo^j-6'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.security.apps.SecurityConfig',
    'app.core.apps.CoreConfig',
    'app.monitoring.apps.MonitoringConfig',
    'app.threat_management.apps.ThreatManagementConfig',
    'app.alarm.apps.AlarmConfig',
    'livereload',
    'widget_tweaks',
    'storages',
]

NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'livereload.middleware.LiveReloadScript',
    'django.middleware.locale.LocaleMiddleware', # Para las traducciones
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n', # Para las traducciones
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'postgres',  # El nombre de la base de datos que especificaste
#         'USER': 'postgres',  # O el nombre de usuario que estableciste
#         'PASSWORD': 'postgres',  # La contraseña que estableciste
#         'HOST': 'database-1.cf66s8o8e8mz.us-east-2.rds.amazonaws.com',  # Reemplaza con tu endpoint real
#         'PORT': '5432',
#     }
# }

AWS_REGION = 'us-east-2'

# Configuración de AWS S3
AWS_ACCESS_KEY_ID = 'AKIAVFIWI5XGD62N765E'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'proyecto-final-imagenes'
AWS_S3_REGION_NAME = 'us-east-2'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_QUERYSTRING_AUTH = False

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "default_acl": None,
            "querystring_auth": False,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "signature_version": "s3v4",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Configuración de archivos media
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de archivos estáticos locales
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

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

LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'security.User'
LOGIN_URL = '/security/auth/login'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

SESSION_COOKIE_AGE = 1800  # 30 minutos en segundos
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# SECCIÓN DE CORREOS
# Configuración de correo
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'pasysalert@gmail.com'
EMAIL_HOST_PASSWORD = 'lvin mgql hwbm gdes'

# Configuracion para las traducciones
USE_I18N = True
LANGUAGES = [
    ('es', 'Spanish'),
    ('en', 'English'),
]
LANGUAGE_CODE = 'es'
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
