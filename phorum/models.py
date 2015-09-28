from autoslug.fields import AutoSlugField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    username = models.CharField(max_length=32, unique=True, error_messages={
            'unique': _("A user with that username already exists."),
        })
    email = models.EmailField(_('email address'), blank=True)

    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    kredyti = models.PositiveIntegerField(default=0)
    level_override = models.PositiveSmallIntegerField(null=True, blank=True)
    motto = models.CharField(max_length=64, blank=True)
    avatar = models.ImageField(upload_to="avatars", blank=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def level(self):
        if self.level_override is not None:
            return self.level_override

        if self.kredyti > 35000:
            return 8
        elif self.kredyti > 20000:
            return 7
        elif self.kredyti > 10000:
            return 6
        elif self.kredyti > 6000:
            return 5
        elif self.kredyti > 3000:
            return 4
        elif self.kredyti > 1100:
            return 3
        elif self.kredyti > 400:
            return 2
        elif self.kredyti > 150:
            return 1
        return 0


class Room(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = AutoSlugField(populate_from='name')
    author = models.ForeignKey(User, related_name="created_rooms", null=True, blank=True)
    moderator = models.ForeignKey(User, related_name="moderated_rooms", null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128, blank=True)
    visits = models.ManyToManyField(User, through="RoomVisit")
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ('-pinned', 'name')

    def __unicode__(self):
        return self.name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)


class RoomVisit(models.Model):
    room = models.ForeignKey(Room)
    user = models.ForeignKey(User)
    visit_time = models.DateTimeField(auto_now=True)


class LastReplyField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        if not model_instance.pk and not model_instance.thread:
            return model_instance.created
        return super(LastReplyField, self).pre_save(model_instance, add)


class Message(models.Model):
    thread = models.ForeignKey("self", null=True, blank=True, db_index=True,
                               related_name="children")
    author = models.ForeignKey(User, related_name="posted_%(class)s")
    recipient = models.ForeignKey(User, related_name="received_%(class)s", blank=True, null=True)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    last_reply = LastReplyField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['created']

    @property
    def thread_reply_id(self):
        return self.thread_id or self.pk


class PublicMessage(Message):
    room = models.ForeignKey(Room)

    def save(self, *args, **kwargs):
        super(PublicMessage, self).save(*args, **kwargs)
        if self.thread:
            # update last_reply on parent
            root = PublicMessage.objects.get(pk=self.thread.pk)
            root.last_reply = self.created
            root.save()
        return self


class PrivateMessage(Message):
    pass
