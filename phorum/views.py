# coding=utf-8
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import login as auth_login
from django.core.paginator import Paginator
from django.db.models import Count, Max
from django.shortcuts import redirect, render, get_object_or_404

from .forms import LoginForm, PublicMessageForm
from .models import PublicMessage, Room, RoomVisit


def room_view(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

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

    if request.user.is_authenticated():
        visit, created = RoomVisit.objects.get_or_create(user=request.user, room=room)
        if not created:
            # just update the time
            visit.save()

        if request.method == "POST":
            if message_form.is_valid():
                message_form.save(author=request.user, room=room)
                return redirect("room_view", room_slug=room.slug)

    return render(request, "phorum/room_view.html", {
        'pagination': current_page,
        'threads': threads,
        'message_form': PublicMessageForm(request.POST or None),
        'login_form': LoginForm(),
    })


def room_list(request):
    rooms = Room.objects.annotate(total_messages=Count("publicmessage"),
                                  last_message_time=Max("publicmessage__created"))

    visits = None
    if request.user.is_authenticated():
        visits = RoomVisit.objects.filter(user=request.user).extra(
            select={
                'new_messages': 'SELECT COUNT(*) FROM "phorum_publicmessage" '
                                'WHERE "phorum_publicmessage"."created" > "phorum_roomvisit"."visit_time" '
                                'AND "phorum_publicmessage"."room_id" = "phorum_roomvisit"."room_id"'
            }
        ) \
            .values_list("room", "new_messages")
        visits = dict(visits)

    return render(request, "phorum/room_list.html", {
        'rooms': rooms,
        'login_form': LoginForm(),
        'visits': visits,
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
