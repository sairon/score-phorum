from django import template

register = template.Library()


@register.filter
def new_posts(room, visits):
    if not visits:
        return room.total_messages
    return visits.get(room.id, room.total_messages)


@register.filter
def is_newer_than(message, compared_time=None):
    if not compared_time:
        return True
    return message.created > compared_time


@register.filter
def can_be_deleted_by(message, user):
    return message.can_be_deleted_by(user)
