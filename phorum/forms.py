# coding=utf-8
import os
from autoslug.settings import slugify
from captcha.fields import ReCaptchaField
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm as DefaultUserChangeForm,
    UserCreationForm as DefaultUserCreationForm
)
from django.contrib.auth.hashers import check_password
from django.db.models.fields.files import ImageFieldFile
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
import floppyforms.__future__ as forms

from .models import PrivateMessage, PublicMessage, Room, User, UserRoomKeyring


class AvatarImageField(forms.ImageField):
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


class BaseMessageForm(forms.ModelForm):
    recipient = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'placeholder': "adresát"}))

    class Meta:
        fields = ('recipient', 'text', 'thread')
        widgets = {
            'thread': forms.HiddenInput,
            'text': forms.Textarea(attrs={'placeholder': "text"}),
        }

    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('author')
        super(BaseMessageForm, self).__init__(*args, **kwargs)

    def clean_recipient(self):
        recipient_name = self.cleaned_data.get("recipient") or None
        recipient = None
        try:
            recipient = User.objects.get(username__iexact=recipient_name)
        except User.DoesNotExist:
            if recipient_name is not None:
                raise forms.ValidationError(u"Uživatel s přezdívkou '%s' neexistuje." % recipient_name)
        return recipient

    def save(self, commit=True):
        message = super(BaseMessageForm, self).save(False)
        message.author = self.author
        if commit:
            message.save()
        return message


class PrivateMessageForm(BaseMessageForm):
    error_messages = {
        'invalid_thread': u"Není možné zaslat zprávu do požadovaného vlákna."
    }

    def __init__(self, *args, **kwargs):
        super(PrivateMessageForm, self).__init__(*args, **kwargs)
        self.fields['recipient'].required = True

    class Meta(BaseMessageForm.Meta):
        model = PrivateMessage

    def clean_thread(self):
        thread = self.cleaned_data.get('thread')
        if thread:
            if self.author not in (thread.author, thread.recipient):
                raise forms.ValidationError(
                    self.error_messages['invalid_thread'],
                    code='invalid_thread',
                )
        return thread


class PublicMessageForm(BaseMessageForm):
    to_inbox = forms.BooleanField(required=False)

    class Meta(BaseMessageForm.Meta):
        model = PublicMessage
        fields = ('recipient', 'to_inbox', 'text', 'thread')

    def save(self, commit=True, room=None):
        message = super(PublicMessageForm, self).save(False)
        message.room = room
        if commit:
            message.save()
        return message


class LoginForm(AuthenticationForm):
    pass


class AdminUserChangeForm(DefaultUserChangeForm):
    class Meta(DefaultUserChangeForm.Meta):
        model = User


class AvatarInput(forms.widgets.ClearableFileInput):
    template_name = "widgets/avatar.html"


class UserChangeForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
        'password_incorrect': _("Your old password was entered incorrectly. "
                                "Please enter it again."),
    }
    avatar = AvatarImageField(required=False,
                              widget=AvatarInput)
    old_password = forms.CharField(label=_("Old password"),
                                   required=False,
                                   widget=forms.PasswordInput)
    new_password1 = forms.CharField(label=_("New password"),
                                    required=False,
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    required=False,
                                    widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'motto', 'avatar', 'max_thread_roots')

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data.get("old_password")

        # check old password only if user is trying to change the password
        if old_password and not self.instance.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def clean(self):
        old_password = self.cleaned_data.get("old_password")
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and not old_password:
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        if (password1 and not password2) or (password2 and not password1):
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(False)
        if self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user


class UserCreationForm(DefaultUserCreationForm):
    captcha = ReCaptchaField()

    class Meta(DefaultUserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'motto', 'password1', 'password2', 'captcha')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                User._meta.get_field('username').error_messages['unique'],
                code='unique',
            )
        return username


class RoomCreationForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data['name'].strip()
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
