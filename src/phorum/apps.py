from django.apps import AppConfig
from django.db.models.fields import Field


class PhorumConfig(AppConfig):
    name = 'phorum'

    def ready(self):
        from .models import UnaccentIRegex
        Field.register_lookup(UnaccentIRegex)
