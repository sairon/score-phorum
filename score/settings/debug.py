from .base import *

DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
)

SENDFILE_BACKEND = "sendfile.backends.development"

MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE_CLASSES


EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
