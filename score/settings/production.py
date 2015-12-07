from .base import *

DEBUG = False

del TEMPLATES[0]['APP_DIRS']
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ])]

ALLOWED_HOSTS = ["www.scorephorum.cz", "beta.scorephorum.cz", "localhost"]

ADMINS = (
    ("Jan Cermak", "sairon@sairon.cz"),
)
