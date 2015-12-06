from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def new_posts(room, visits):
    if not visits:
        return None
    return visits.get(room.id, room.total_messages)


@register.filter
def can_be_deleted_by(message, user):
    return message.can_be_deleted_by(user)


@register.filter
def nl2br(text):
    return mark_safe(text.strip().replace("\n", "<br>"))
