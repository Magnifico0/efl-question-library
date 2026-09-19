from .base import * 
DEBUG = True

ALLOWED_HOSTS = ['*']
# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#efl_user:efl_password@db:5432/efl_db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':   'efl_db',
        'USER': 'efl_user',
        'PASSWORD': 'efl_password',
        'HOST' : 'db',
        'PORT' : '5432', 
    }

}

# settings.py dosyasının en altına ekle:

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

#DEV tools 
INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",
    "silk",
    "nplusone.ext.django"
]

MIDDLEWARE +=[
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE,
    "silk.middleware.SilkyMiddleware",
    "nplusone.ext.django.NPlusOneMiddleware",
]

#debug toolbar'ın görünmesi için 
import socket 
hostname, _ , ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")]+ ".1" for ip in ips]+ ["127.0.0.1"]

#nplusone : only log not throw error 
import logging 
NPLUSONE_RAISE = False
NPLUSONE_LOGGER = logging.getLogger("nplusone")
NPLUSONE_LOG_LEVEL = logging.WARNING