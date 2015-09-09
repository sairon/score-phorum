from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nickname = models.CharField(max_length=32, unique=True)
    kredyti = models.IntegerField()
    avatar = models.ImageField()


class Room(models.Model):
    name = models.CharField(max_length=64, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)


class RoomVisit(models.Model):
    room = models.ForeignKey(Room)
    user = models.ForeignKey(User)
    visit_time = models.DateTimeField(auto_now=True)


class Message(models.Model):
    author = models.ForeignKey(User)
    text = models.TextField()
    parent = models.ForeignKey("self")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class PublicMessage(Message):
    room = models.ForeignKey(Room)


class PrivateMessage(Message):
    recipient = models.ForeignKey(User)
