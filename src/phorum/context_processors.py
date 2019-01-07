from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now
from user_sessions.models import Session

from .models import PrivateMessage


def inbox_messages(request):
    inbox_unread_count = 0
    if request.user.is_authenticated():
        # get all messages to/from this user
        inbox_unread_count = PrivateMessage.objects \
            .filter(Q(author=request.user) | Q(recipient=request.user))

        # inbox visit time can be empty
        if request.user.inbox_visit_time:
            inbox_unread_count = inbox_unread_count \
                .filter(created__gte=request.user.inbox_visit_time)
        # get count
        inbox_unread_count = inbox_unread_count.count()

    return {
        'inbox_unread_count': inbox_unread_count
    }


def active_users(request):
    active_threshold = now() - timedelta(minutes=settings.ACTIVE_USERS_TIMEOUT)

    active_users_count = Session.objects\
        .filter(user__isnull=False, expire_date__gte=now(), last_activity__gte=active_threshold)\
        .distinct('user__username')\
        .count()

    return {
        'active_users_count': active_users_count
    }
