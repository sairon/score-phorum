from autoslug.fields import AutoSlugField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models


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


class Message(models.Model):
    thread = models.ForeignKey("self", null=True, blank=True, db_index=True,
                               related_name="children")
    author = models.ForeignKey(User, related_name="posted_%(class)s")
    recipient = models.ForeignKey(User, related_name="received_%(class)s", blank=True, null=True)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    last_reply = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['created']


class PublicMessage(Message):
    room = models.ForeignKey(Room)

    def save(self, *args, **kwargs):
        if not self.pk and not self.thread:
            self.last_reply = self.created
        super(PublicMessage, self).save(*args, **kwargs)
        if self.thread:
            # update last_reply on parent
            root = PublicMessage.objects.get(pk=self.thread.pk)
            root.last_reply = self.created
            root.save()
        return self


class PrivateMessage(Message):
    pass
