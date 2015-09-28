#!/usr/bin/env python
# run as: dropdb score && createdb -O score score && ./manage.py syncdb --noinput && PYTHONPATH=.:$PYTHONPATH ./dev/migrate_data.py

from datetime import datetime
from django import setup
from django.db import connection, transaction

import MySQLdb as mysql
from MySQLdb.cursors import DictCursor
from pytz import timezone

from phorum.models import Room, PublicMessage, User


setup()


tz = timezone("Europe/Prague")


def unescape(text):
    return text.replace("\%", "%").replace("\_", "_")


class OldRoom(object):
    def __init__(self, title):
        self.title = title
        self.threads = {}
        self.author = None
        self.moderator = None
        self.created = None
        self._instance = None

    def create_instance(self):
        self._instance = Room.objects.create(
            name=self.title
        )
        return self._instance

    @property
    def instance(self):
        return self._instance


class Thread(object):
    def __init__(self, old_id):
        self.old_id = old_id
        self.comments = []


class Comment(object):
    def __init__(self, author, recipient, created, text, thread_id):
        self.author = author
        self.recipient = recipient
        created_time = datetime.strptime(created, "%d.%m. %M:%S")
        created_time.replace(microsecond=thread_id)
        self.created = tz.localize(created_time.replace(year=2014 if created_time.month > 9 else 2015))
        self.text = text
        self.thread_id = thread_id


def main():
    rooms = {}

    conn = mysql.connect(host="localhost", user="root", passwd="root", db="score", cursorclass=DictCursor)
    c = conn.cursor()
    c.execute("SET CHARACTER SET utf8")

    c.execute("SELECT * FROM mistnosti WHERE stranka = 0")
    for row in c:
        rooms[row['id']] = OldRoom(row['nazev'])

    users = set()

    c.execute("SELECT * FROM prispevky ORDER BY thread, thread_id")
    for row in c:
        thread = rooms[row['mistnost']].threads.setdefault(row['thread'], Thread(old_id=row['thread']))
        thread.comments.append(Comment(unescape(row['od']), unescape(row['pro']), row['cas'], unescape(row['text']), row['thread_id']))
        users.add(unescape(row['od']))
        users.add(unescape(row['pro']))

    c.close()

    user_instances = {}

    for user in users:
        if user != "all":
            user_instances[user] = User.objects.create(
                username=user
            )

    for room_id, room in rooms.iteritems():
        room.create_instance()

    for room in rooms.itervalues():
        with transaction.atomic():
            for thread in room.threads.itervalues():
                thread_parent = None
                if len(thread.comments) == 1 and thread.comments[0].author in ("kekut", "syrsky_imikrant"):
                    continue
                for comment in thread.comments:
                    inst = PublicMessage.objects.create(
                        room=room.instance,
                        text=comment.text,
                        author=user_instances[comment.author],
                        recipient=None if comment.recipient == "all" else user_instances[comment.recipient],
                        thread=thread_parent,
                        created=comment.created
                    )
                    if comment.thread_id == 0:
                        thread_parent = inst

    print "Performing final optimization..."
    connection.cursor().execute("VACUUM FULL")


if __name__ == "__main__":
    main()
