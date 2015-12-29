def user_can_view_protected_room(user, room):
    from .models import UserRoomKeyring

    try:
        record = UserRoomKeyring.objects.get(user=user, room=room)
        if room.password_changed < record.last_successful_entry:
            return True
    except UserRoomKeyring.DoesNotExist:
        return False
    return False


def get_ip_addr(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_addr = x_forwarded_for.split(",")[0]
    else:
        ip_addr = request.META.get("REMOTE_ADDR")
    return ip_addr
