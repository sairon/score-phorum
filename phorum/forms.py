from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm as DefaultUserChangeForm,
    UserCreationForm as DefaultUserCreationForm
)

from .models import PublicMessage, User


class PublicMessageForm(forms.ModelForm):
    parent = forms.IntegerField(required=False, widget=forms.TextInput)  # TODO: JS populated HiddenInput

    class Meta:
        fields = ('text', )
        model = PublicMessage

    def save(self, commit=True, author=None, room=None):
        message = super(PublicMessageForm, self).save(False)
        message.author = author
        parent_id = self.cleaned_data.get("parent")
        if parent_id:
            ancestor = PublicMessage.objects.get(pk=parent_id)
            # if the sent message is a reply, then ancestor's thread_id
            # contains the root node's PK, otherwise it's simply PK of ancestor
            message.thread_id = ancestor.thread_id or ancestor.pk
            message.recipient = ancestor.author
            message.room = ancestor.room
        else:
            message.room = room
        if commit:
            message.save()
        return message


class LoginForm(AuthenticationForm):
    pass


class UserChangeForm(DefaultUserChangeForm):
    class Meta(DefaultUserChangeForm.Meta):
        model = User


class UserCreationForm(DefaultUserCreationForm):
    class Meta(DefaultUserCreationForm.Meta):
        model = User
