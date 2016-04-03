from bleach import clean, linkify
from django.db import models
from django.template.defaultfilters import linebreaksbr
from django.utils.safestring import mark_safe
from django_bleach.models import BleachField

from .. import form_fields


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


class RawContentFileField(models.FileField):
    def formfield(self, **kwargs):
        defaults = {'form_class': form_fields.RawContentFileField, 'max_length': self.max_length}
        defaults.update(kwargs)
        return super(RawContentFileField, self).formfield(**defaults)

    def save_form_data(self, instance, data):
        # Important: None means "no change", other false value means "clear"
        # This subtle distinction (rather than a more explicit marker) is
        # needed because we need to consume values that are also sane for a
        # regular (non Model-) Form to find in its cleaned_data dictionary.
        if data is not None:
            # This value will be converted to unicode and stored in the
            # database, so leaving False as-is is not acceptable.
            if not data:
                data = ''
                file = getattr(instance, self.name)
                if file and file.path:
                    # Try to delete the file. Case when the file does not
                    # exist is handled by the delete method of the storage.
                    self.storage.delete(file.path)
            setattr(instance, self.name, data)
