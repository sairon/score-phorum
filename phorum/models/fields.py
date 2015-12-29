from bleach import clean, linkify
from django.db import models
from django.template.defaultfilters import linebreaksbr
from django.utils.safestring import mark_safe
from django_bleach.models import BleachField


class LastReplyField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        if not model_instance.pk and not model_instance.thread:
            return model_instance.created
        return super(LastReplyField, self).pre_save(model_instance, add)


class MessageTextField(BleachField):
    """Bleach field extended with nl2br transformation before saving."""

    def pre_save(self, model_instance, add):
        message = getattr(model_instance, self.attname).strip()
        message = linebreaksbr(mark_safe(message))
        if "<a" not in message:
            message = linkify(message)
        return clean(message, **self.bleach_kwargs)
