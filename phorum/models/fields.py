from django.db import models
from django_bleach.models import BleachField

from ..utils import nl2br


class LastReplyField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        if not model_instance.pk and not model_instance.thread:
            return model_instance.created
        return super(LastReplyField, self).pre_save(model_instance, add)


class MessageTextField(BleachField):
    """Bleach field extended with nl2br transformation before saving."""

    def pre_save(self, model_instance, add):
        return nl2br(super(MessageTextField, self).pre_save(model_instance, add))
