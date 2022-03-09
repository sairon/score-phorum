# coding=utf-8
import os

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_text
from django.utils.html import conditional_escape


class AvatarInput(forms.widgets.ClearableFileInput):
    template_name = "widgets/avatar.html"


class AvatarImageField(forms.ImageField):
    widget = AvatarInput
    valid_extensions = ('jpg', 'jpeg', 'gif', 'png')
    valid_content_types = {
        'image/jpeg': (".jpg", ".jpeg"),
        'image/gif': (".gif",),
        'image/png': (".png",),
    }
    max_image_size = 15 * 1024  # bytes

    def __init__(self, *args, **kwargs):
        super(AvatarImageField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(AvatarImageField, self).clean(*args, **kwargs)
        if data and not isinstance(data, ImageFieldFile):
            if data.content_type not in self.valid_content_types:
                raise forms.ValidationError(u'Ikona není v přijatelném formátu (GIF, JPEG nebo PNG).')
            if data.image.size != (40, 50):
                raise forms.ValidationError(u'Ikona musí mít rozměry 40 x 50 px.')
            if data.size > self.max_image_size:
                raise forms.ValidationError(u'Ikona je příliš velká (%s), maximální povolená velikost je %s.'
                                            % (filesizeformat(data.size), filesizeformat(self.max_image_size)))
            ext = os.path.splitext(data.name)[1]
            if ext.lower() not in self.valid_content_types[data.content_type]:
                raise forms.ValidationError(u'Ikona má nesprávnou příponu.')

        return data


class EditableFileTextarea(forms.widgets.Input):
    template_name = "django/forms/widgets/textarea.html"
    rows = 20
    cols = 100

    def __init__(self, attrs=None):
        default_attrs = {'cols': self.cols, 'rows': self.rows}
        if attrs:
            default_attrs.update(attrs)
        super(EditableFileTextarea, self).__init__(default_attrs)

    def _format_value(self, value):
        return conditional_escape(force_text(value))

    def render(self, name, value, attrs=None, renderer=None):
        try:
            value = value and value.read().decode("utf-8")  # read only non-empty fields
        except IOError:
            value = ""
        return super(EditableFileTextarea, self).render(name, value or "", attrs=attrs, renderer=renderer)


class RawContentFileField(forms.FileField):
    widget = EditableFileTextarea

    def clean(self, data, initial=None):
        # False means the field value should be cleared; further validation is
        # not needed.
        if not data:
            if not self.required:
                return False
            data = None
        if not data and initial:
            return initial
        data = self.to_python(data)
        self.validate(data)
        self.run_validators(data)
        return data

    def to_python(self, data):
        data = ContentFile(data)
        data.name = "_"  # MUST NOT be empty to pass bool(self) check of File

        try:
            file_size = data.size
        except AttributeError:
            raise ValidationError(self.error_messages['invalid'], code='invalid')

        if not self.allow_empty_file and not file_size:
            raise ValidationError(self.error_messages['empty'], code='empty')

        return data
