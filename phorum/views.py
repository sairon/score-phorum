from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from .forms import PublicMessageForm
from .models import PublicMessage, Room


def room_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    page_number = request.GET.get("page", 1)

    root_messages = PublicMessage.objects.filter(room=room) \
        .filter(parent=None)\
        .order_by('-created')\
        .values_list("tree_id", flat=True)

    paginator = Paginator(root_messages, 10)
    current_page = paginator.page(page_number)

    messages = PublicMessage.objects.filter(tree_id__in=current_page.object_list) \
        .prefetch_related('author')

    message_form = PublicMessageForm(request.POST or None)

    if request.method == "POST":
        if message_form.is_valid():
            message_form.save(author=request.user, room=room)
            return redirect("room_view", room_id=room.id)

    return render(request, "phorum/room_view.html", {
        'pagination': current_page,
        'messages': messages,
        'message_form': PublicMessageForm(request.POST or None),
    })


def room_list(request):
    rooms = Room.objects.all()
    return render(request, "phorum/room_list.html", {
        'rooms': rooms,
    })
