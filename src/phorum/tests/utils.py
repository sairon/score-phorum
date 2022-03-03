from django.utils import timezone

from ..models import PublicMessage


def new_public_thread(room, author, recipient=None, text=None, created=None):
    """Tests helper for creating new threads in rooms."""
    msg = PublicMessage.objects.create(
            room=room, author=author, recipient=recipient,
            text=text or "text"
    )
    if created:
        # would be ignored in created() because of auto_now_add=True
        msg.created = created
        msg.save()
    return msg


def public_reply(parent_message, author, recipient=None, text=None, created=None):
    """Tests helper for creating replies to existing messages."""
    msg = PublicMessage.objects.create(
            room=parent_message.room, author=author,
            recipient=recipient or parent_message.author,
            text=text or "text"
    )
    if created:
        # would be ignored in created() because of auto_now_add=True
        msg.created = created
        msg.save()
    return msg
