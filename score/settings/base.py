import os
import json

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# load settings file with secrets
with open(os.path.join(BASE_DIR, "score", "settings", "local_settings.json")) as f:
    local_settings = json.loads(f.read())


def get_local_setting(setting, default=None, local_settings=local_settings):
    """
    Method for fetching local settings from settings file.

    Default value can be specified, but must not be None.
    """
    try:
        return local_settings[setting]
    except KeyError:
        if default is not None:
            return default
        raise ImproperlyConfigured("Missing settings value '%s'" % setting)


SECRET_KEY = get_local_setting("SECRET_KEY")

DEBUG = False
ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'user_sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',
    'django_bleach',
    'floppyforms',
    'phorum',
)

MIDDLEWARE_CLASSES = (
    'user_sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'phorum.middleware.UserActivityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

SESSION_ENGINE = 'user_sessions.backends.db'

ROOT_URLCONF = 'score.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'phorum.context_processors.active_users',
                'phorum.context_processors.inbox_messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'score.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': get_local_setting("DB_HOST", default=""),
        'NAME': get_local_setting("DB_NAME"),
        'USER': get_local_setting("DB_USER"),
        'PASSWORD': get_local_setting("DB_PASSWORD"),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'cs'

TIME_ZONE = 'Europe/Prague'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = '/media/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = '/static/'

AUTH_USER_MODEL = 'phorum.User'

AUTHENTICATION_BACKENDS = ('phorum.backends.CaseInsensitiveModelBackend',)

LOGIN_URL = "/"
LOGOUT_URL = "/logout"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler'
        },

    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    }
}


BLEACH_ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'font', 'br', 'img', 'sub', 'sup', 'marquee']
BLEACH_ALLOWED_ATTRIBUTES = ['href', 'title', 'style', 'color', 'src']

BLEACH_ALLOWED_STYLES = [
    'font-family', 'font-weight', 'text-decoration', 'font-variant'
]

BLEACH_STRIP_TAGS = False
BLEACH_STRIP_COMMENTS = True

RECAPTCHA_PUBLIC_KEY = "6LfmexMTAAAAAEArc6dCfDk8N5VCcX_8s3k2LXMy"
RECAPTCHA_PRIVATE_KEY = get_local_setting("RECAPTCHA_PRIVATE_KEY", "")
NOCAPTCHA = True
RECAPTCHA_USE_SSL = True


ACTIVE_USERS_TIMEOUT = 20  # minutes
