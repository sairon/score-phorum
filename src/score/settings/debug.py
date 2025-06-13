from .base import *

DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
)

SENDFILE_BACKEND = "sendfile.backends.development"

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE

# Use default Google test keys and silence error
del RECAPTCHA_PUBLIC_KEY
del RECAPTCHA_PRIVATE_KEY
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: True
}
