from .models import UserRoomKeyring


def user_can_view_protected_room(user, room):
    try:
        record = UserRoomKeyring.objects.get(user=user, room=room)
        if room.password_changed < record.last_successful_entry:
            return True
    except UserRoomKeyring.DoesNotExist:
        return False
    return False
