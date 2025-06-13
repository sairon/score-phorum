from .production import *

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Use default Google test keys and silence error
del RECAPTCHA_PUBLIC_KEY
del RECAPTCHA_PRIVATE_KEY
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
