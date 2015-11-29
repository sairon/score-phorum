from django import template
from django.utils.html import escape

register = template.Library()


@register.simple_tag
def new_posts(room, visits):
    return escape(visits.get(room.id, room.total_messages))


@register.filter
def can_be_deleted_by(message, user):
    return message.can_be_deleted_by(user)
