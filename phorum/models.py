from autoslug.fields import AutoSlugField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from .managers import PublicMessageQuerySet


class User(AbstractUser):
    nickname = models.CharField(max_length=32, unique=True)
    kredyti = models.IntegerField(default=0)
    avatar = models.ImageField()


class Room(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = AutoSlugField(populate_from='name')
    author = models.ForeignKey(User, related_name="created_rooms", null=True, blank=True)
    moderator = models.ForeignKey(User, related_name="moderated_rooms", null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128, blank=True)
    visits = models.ManyToManyField(User, through="RoomVisit")
    pinned = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)


class RoomVisit(models.Model):
    room = models.ForeignKey(Room)
    user = models.ForeignKey(User)
    visit_time = models.DateTimeField(auto_now=True)


class Message(MPTTModel):
    author = models.ForeignKey(User)
    text = models.TextField()
    parent = TreeForeignKey("self", null=True, blank=True, db_index=True,
                            related_name="children")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ['-created']


class PublicMessage(Message):
    objects = PublicMessageQuerySet.as_manager()

    room = models.ForeignKey(Room)


class PrivateMessage(Message):
    recipient = models.ForeignKey(User, related_name="received_message")
