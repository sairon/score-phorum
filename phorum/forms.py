# coding=utf-8
import os
from autoslug.settings import slugify
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm as DefaultUserChangeForm,
    UserCreationForm as DefaultUserCreationForm
)
from django.contrib.auth.hashers import check_password
from django.db.models.fields.files import ImageFieldFile
from django.template.defaultfilters import filesizeformat

from .models import PrivateMessage, PublicMessage, Room, User, UserRoomKeyring


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


class BaseMessageForm(forms.ModelForm):
    recipient = forms.CharField(required=False)

    class Meta:
        fields = ('recipient', 'text', 'thread')
        widgets = {
            'thread': forms.HiddenInput,
            'recipient': forms.TextInput,
        }

    def clean_recipient(self):
        recipient_name = self.cleaned_data.get("recipient") or None
        recipient = None
        try:
            recipient = User.objects.get(username=recipient_name)
        except User.DoesNotExist:
            if recipient_name is not None:
                raise forms.ValidationError(u"Uživatel s přezdívkou '%s' neexistuje." % recipient_name)
        return recipient

    def save(self, commit=True, author=None):
        message = super(BaseMessageForm, self).save(False)
        message.author = author
        if commit:
            message.save()
        return message


class PrivateMessageForm(BaseMessageForm):
    class Meta(BaseMessageForm.Meta):
        model = PrivateMessage


class PublicMessageForm(BaseMessageForm):
    class Meta(BaseMessageForm.Meta):
        model = PublicMessage

    def save(self, commit=True, author=None, room=None):
        message = super(PublicMessageForm, self).save(False, author=author)
        message.room = room
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

    class Meta:
        model = User
        fields = ('email', 'motto', 'avatar')


class UserCreationForm(DefaultUserCreationForm):
    class Meta(DefaultUserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'motto')


class RoomCreationForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data['name']
        if Room.objects.filter(slug__exact=slugify(name)).count() > 0:
            raise forms.ValidationError(u"Místnost s podobným názvem již existuje.")
        return name

    def save(self, commit=True, author=None):
        if not author:
            raise AttributeError("Při vytváření místnosti došlo k chybě - místnost musí mít autora.")
        room = super(RoomCreationForm, self).save(False)
        room.author = author
        room.set_password(self.cleaned_data['password'])
        if commit:
            room.save()
        return room

    class Meta:
        model = Room
        fields = ('name', 'password', 'moderator')


class RoomChangeForm(forms.ModelForm):
    password = forms.CharField(label="Nové heslo", required=False, widget=forms.PasswordInput)
    clear_password = forms.BooleanField(label="Odstranit heslo", required=False)

    def save(self, commit=True):
        room = super(RoomChangeForm, self).save(False)
        new_password = self.cleaned_data['password']
        if self.cleaned_data['clear_password']:
            room.set_password("")
        elif new_password:
            room.set_password(new_password)
        if commit:
            room.save()
        return room

    class Meta:
        model = Room
        fields = ('password', 'clear_password', 'moderator')


class RoomPasswordPrompt(forms.Form):
    password = forms.CharField(required=True, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop("room")
        self.user = kwargs.pop("user")
        super(RoomPasswordPrompt, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not check_password(password, self.room.password):
            raise forms.ValidationError(u"Heslo je neplatné.")

        # save entry to keyring
        keyring_record, created = UserRoomKeyring.objects.get_or_create(room=self.room, user=self.user)
        if not created:
            # save to update time
            keyring_record.save()

        return password
