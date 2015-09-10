from django.shortcuts import redirect, render, get_object_or_404

from .forms import PublicMessageForm
from .models import PublicMessage, Room


def room_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    parent_messages = PublicMessage.objects.filter(room=room) \
        .prefetch_related('author') \
        .order_by('tree_id', 'lft')

    message_form = PublicMessageForm(request.POST or None)

    if request.method == "POST":
        if message_form.is_valid():
            message_form.save(author=request.user, room=room)
            return redirect("room_view", room_id=room.id)

    return render(request, "phorum/room_view.html", {
        'parent_messages': parent_messages,
        'message_form': PublicMessageForm(request.POST or None),
    })


def room_list(request):
    rooms = Room.objects.all()
    return render(request, "phorum/room_list.html", {
        'rooms': rooms,
    })
