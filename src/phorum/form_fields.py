from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.encoding import force_text
from django.utils.html import conditional_escape

import floppyforms.__future__ as forms


class EditableFileTextarea(forms.widgets.Input):
    template_name = 'floppyforms/textarea.html'
    rows = 20
    cols = 100

    def __init__(self, attrs=None):
        default_attrs = {'cols': self.cols, 'rows': self.rows}
        if attrs:
            default_attrs.update(attrs)
        super(EditableFileTextarea, self).__init__(default_attrs)

    def _format_value(self, value):
        return conditional_escape(force_text(value))

    def render(self, name, value, attrs=None, **kwargs):
        try:
            value = value and value.read()  # read only non-empty fields
        except IOError:
            value = ""
        return super(EditableFileTextarea, self).render(name, value, attrs=attrs, **kwargs)


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
