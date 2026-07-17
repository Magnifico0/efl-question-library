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