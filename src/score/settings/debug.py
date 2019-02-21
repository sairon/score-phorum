from .base import *

DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
)

SENDFILE_BACKEND = "sendfile.backends.development"

MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE_CLASSES

# Use default Google test keys and silence error
del RECAPTCHA_PUBLIC_KEY
del RECAPTCHA_PRIVATE_KEY
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: True
}
