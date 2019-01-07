from ..models import PublicMessage


def new_public_thread(room, author, recipient=None, text=None):
    """Tests helper for creating new threads in rooms."""
    text = text or "text"
    return PublicMessage.objects.create(
            room=room, author=author, recipient=recipient,
            text=text
    )


def public_reply(parent_message, author, recipient=None, text=None):
    """Tests helper for creating replies to existing messages."""
    text = text or "text"
    return PublicMessage.objects.create(
            room=parent_message.room, author=author,
            recipient=recipient or parent_message.author,
            text=text
    )
