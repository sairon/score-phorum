from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import PublicMessage


class PublicMessageForm(forms.ModelForm):
    class Meta:
        fields = ('text',)
        model = PublicMessage

    def save(self, commit=True, author=None, room=None):
        message = super(PublicMessageForm, self).save(False)
        message.author = author
        if message.parent:
            message.room = message.parent.room
        else:
            message.room = room
        if commit:
            message.save()
        return message


class LoginForm(AuthenticationForm):
    pass
