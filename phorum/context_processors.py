from django.db.models import Q

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
