#!/usr/bin/env python
from django import setup
setup()

##################

import random


from faker import Faker

from phorum.models import (
    PublicMessage,
    Room,
    User
)

fake = Faker()


def generate_user():
    """Generate fake PersonTurrisUser.

    :return: instance of created user
    """
    return User.objects.create_user(
        username=fake.word(),
        email=fake.email(),
        nickname=fake.name()
    )


def generate_room():
    return Room.objects.create(
        name=fake.text(max_nb_chars=64)
    )


def create_message(room, author, parent=None):
    return PublicMessage.objects.create(
        room=room,
        author=author,
        parent=parent,
        text="\n".join(fake.paragraphs(nb=fake.random_int(1, 4)))
    )


def post_to_room(room, users):
    top_messages = [create_message(room, random.choice(users)) for _ in range(0, 50)]

    for parent in top_messages:
        inserted = []
        for _ in range(0, fake.random_int(max=20)):
            inserted.append(create_message(room, random.choice(users), random.choice(inserted + [parent])))


def main():
    users = [generate_user() for _ in range(0, 5)]
    rooms = [generate_room() for _ in range(0, 3)]
    for room in rooms:
        post_to_room(room, users)


if __name__ == "__main__":
    main()
