from django import template
from django.utils.html import escape

register = template.Library()


@register.simple_tag
def new_posts(room, visits):
    return escape(visits.get(room.id, room.total_messages))
