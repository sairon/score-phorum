from django.db import models
from django.template.defaultfilters import linebreaksbr
from django_bleach.models import BleachField


class LastReplyField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        if not model_instance.pk and not model_instance.thread:
            return model_instance.created
        return super(LastReplyField, self).pre_save(model_instance, add)


class MessageTextField(BleachField):
    """Bleach field extended with nl2br transformation before saving."""

    def pre_save(self, model_instance, add):
        return linebreaksbr(super(MessageTextField, self).pre_save(model_instance, add).strip())
