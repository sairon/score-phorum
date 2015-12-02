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

    LEVEL_GREEN = 0
    LEVEL_YELLOW = 1
    LEVEL_ORANGE = 2
    LEVEL_RED = 3
    LEVEL_CRIMSON = 4
    LEVEL_1_DOT = 5
    LEVEL_2_DOTS = 6
    LEVEL_3_DOTS = 7
    LEVEL_GOD = 8
    LEVEL_ADMIN = 15
    LEVEL_EDITOR = 16
    LEVEL_DEV = 99

    LEVELS = (
        (LEVEL_GREEN, "Green ribbon"),
        (LEVEL_YELLOW, "Yellow ribbon"),
        (LEVEL_ORANGE, "Orange ribbon"),
        (LEVEL_RED, "Red ribbon"),
        (LEVEL_CRIMSON, "Crimson ribbon"),
        (LEVEL_1_DOT, "1 dot"),
        (LEVEL_2_DOTS, "2 dots"),
        (LEVEL_3_DOTS, "3 dots"),
        (LEVEL_GOD, "God"),
        (LEVEL_ADMIN, "Admin"),
        (LEVEL_EDITOR, "Editor"),
        (LEVEL_DEV, "Dev"),
    )

    username = models.CharField(max_length=32, unique=True, error_messages={
            'unique': _("A user with that username already exists."),
        })
    email = models.EmailField(_('email address'), blank=True)

    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=False,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    kredyti = models.PositiveIntegerField(default=0)
    level_override = models.PositiveSmallIntegerField(null=True, blank=True, choices=LEVELS)
    motto = models.CharField(max_length=64, blank=True)
    avatar = models.ImageField(upload_to="avatars", blank=True)
    room_keyring = models.ManyToManyField("Room", through="UserRoomKeyring")
    inbox_visit_time = models.DateTimeField(null=True, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)

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

    @property
    def level(self):
        if self.level_override is not None:
            return self.level_override

        if self.kredyti > 35000:
            return User.LEVEL_GOD
        elif self.kredyti > 20000:
            return User.LEVEL_3_DOTS
        elif self.kredyti > 10000:
            return User.LEVEL_2_DOTS
        elif self.kredyti > 6000:
            return User.LEVEL_1_DOT
        elif self.kredyti > 3000:
            return User.LEVEL_CRIMSON
        elif self.kredyti > 1100:
            return User.LEVEL_RED
        elif self.kredyti > 400:
            return User.LEVEL_ORANGE
        elif self.kredyti > 150:
            return User.LEVEL_YELLOW
        return User.LEVEL_GREEN

    def update_inbox_visit_time(self):
        self.inbox_visit_time = timezone.now()
        self.save()


class RoomQueryset(models.QuerySet):
    def pinned(self):
        return self.filter(pinned=True)

    def not_pinned(self):
        return self.filter(pinned=False)


class Room(models.Model):
    objects = RoomQueryset.as_manager()

    name = models.CharField(max_length=64, unique=True)
    slug = AutoSlugField(populate_from='name')
    author = models.ForeignKey(User, related_name="created_rooms", null=True, blank=True)
    moderator = models.ForeignKey(User, related_name="moderated_rooms", null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128, blank=True)
    password_changed = models.DateTimeField(null=True, blank=True)
    visits = models.ManyToManyField(User, through="RoomVisit")
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ('-pinned', 'name')

    def __unicode__(self):
        return self.name

    def set_password(self, raw_password):
        if raw_password:
            self.password = make_password(raw_password)
            self.password_changed = timezone.now()
        else:
            self.password = ""
            self.password_changed = None

    @property
    def protected(self):
        return bool(self.password)


class RoomVisit(models.Model):
    room = models.ForeignKey(Room)
    user = models.ForeignKey(User)
    visit_time = models.DateTimeField(auto_now=True)


class UserRoomKeyring(models.Model):
    room = models.ForeignKey(Room)
    user = models.ForeignKey(User)
    last_successful_entry = models.DateTimeField(auto_now=True)


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

    def can_be_deleted_by(self, user):
        if not user.is_authenticated():
            return False
        if self.author == user:
            return True
        return None


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

    def can_be_deleted_by(self, user):
        can_be_deleted = super(PublicMessage, self).can_be_deleted_by(user)
        if can_be_deleted is not None:
            return can_be_deleted
        elif self.author.level < User.LEVEL_GOD <= user.level:
            # user has at least god level, author's level is lower than god
            return True
        elif user in (self.room.author, self.room.moderator):
            return True
        return False


class PrivateMessage(Message):
    pass
