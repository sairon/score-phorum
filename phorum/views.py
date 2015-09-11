# coding=utf-8
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import login as auth_login
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from .forms import LoginForm, PublicMessageForm
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

    threads = PublicMessage.objects.filter(tree_id__in=current_page.object_list) \
        .prefetch_related('author')

    message_form = PublicMessageForm(request.POST or None)

    if request.method == "POST":
        if message_form.is_valid():
            message_form.save(author=request.user, room=room)
            return redirect("room_view", room_id=room.id)

    return render(request, "phorum/room_view.html", {
        'pagination': current_page,
        'threads': threads,
        'message_form': PublicMessageForm(request.POST or None),
        'login_form': LoginForm(),
    })


def room_list(request):
    rooms = Room.objects.all()
    return render(request, "phorum/room_list.html", {
        'rooms': rooms,
        'login_form': LoginForm(),
    })


def login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
        else:
            messages.error(request, "Neplatný login nebo heslo.")

    return redirect("home")


def logout(request):
    auth_logout(request)
    return redirect("home")
