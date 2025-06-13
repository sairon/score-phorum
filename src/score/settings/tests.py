from .production import *

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Use MD5 password hasher to speed up tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Use default Google test keys and silence error
del RECAPTCHA_PUBLIC_KEY
del RECAPTCHA_PRIVATE_KEY
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
