from .base import *

DEBUG = False

del TEMPLATES[0]['APP_DIRS']
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ])]

ALLOWED_HOSTS = ["scorephorum.cz", "www.scorephorum.cz", "beta.scorephorum.cz"]

ADMINS = (
    ("Jan Cermak", "sairon@sairon.cz"),
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}
