# coding=utf-8
import os
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm as DefaultUserChangeForm,
    UserCreationForm as DefaultUserCreationForm
)
from django.db.models.fields.files import ImageFieldFile
from django.template.defaultfilters import filesizeformat

from .models import PublicMessage, User


class AvatarImageField(forms.ImageField):
    valid_extensions = ('jpg', 'jpeg', 'gif', 'png')
    valid_content_types = {
        'image/jpeg': (".jpg", ".jpeg"),
        'image/gif': (".png",),
        'image/png': (".gif",),
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


class PublicMessageForm(forms.ModelForm):
    thread_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    recipient = forms.CharField(required=False)

    class Meta:
        fields = ('text', )
        model = PublicMessage

    def save(self, commit=True, author=None, room=None):
        message = super(PublicMessageForm, self).save(False)
        message.author = author
        message.room = room
        recipient_name = self.cleaned_data.get("recipient") or None
        recipient = None
        try:
            recipient = User.objects.get(username=recipient_name)
        except User.DoesNotExist:
            if recipient_name is not None:
                raise forms.ValidationError("Uživatel s přezdívkou '%s' neexistuje.")

        message.recipient = recipient

        thread_id = self.cleaned_data.get("thread_id")
        if thread_id:
            message.thread_id = thread_id
        if commit:
            message.save()
        return message


class LoginForm(AuthenticationForm):
    pass


class AdminUserChangeForm(DefaultUserChangeForm):
    class Meta(DefaultUserChangeForm.Meta):
        model = User


class UserChangeForm(forms.ModelForm):
    avatar = AvatarImageField(required=False)

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'motto', 'avatar')


class UserCreationForm(DefaultUserCreationForm):
    class Meta(DefaultUserCreationForm.Meta):
        model = User
