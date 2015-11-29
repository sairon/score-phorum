# coding=utf-8
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.paginator import Paginator
from django.db.models import Count, Max
from django.shortcuts import redirect, render, get_object_or_404

from .forms import LoginForm, PublicMessageForm, UserCreationForm, UserChangeForm
from .models import PublicMessage, Room, RoomVisit


def room_view(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    page_number = request.GET.get("page", 1)

    threads = PublicMessage.objects\
        .filter(room=room, thread=None) \
        .order_by("-last_reply") \
        .prefetch_related("author", "children__author", "children__recipient")

    paginator = Paginator(threads, 10)
    threads = paginator.page(page_number)

    message_form = PublicMessageForm(request.POST or None)

    last_visit_time = None
    if request.user.is_authenticated():
        visit, created = RoomVisit.objects.get_or_create(user=request.user, room=room)
        if not created:
            last_visit_time = visit.visit_time
            # just update the time
            visit.save()

        if request.method == "POST":
            if message_form.is_valid():
                message_form.save(author=request.user, room=room)
                return redirect("room_view", room_slug=room.slug)

    return render(request, "phorum/room_view.html", {
        'threads': threads,
        'last_visit_time': last_visit_time,
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


def message_delete(request, message_id):
    message = get_object_or_404(PublicMessage, pk=message_id)
    message_room_slug = message.room.slug

    if message.can_be_deleted_by(request.user):
        message.delete()
        messages.info(request, "Zpráva byla smazána.")
        return redirect("room_view", room_slug=message_room_slug)
    else:
        messages.error(request, "Nemáte oprávnění ke smazání zprávy.")
        return redirect("room_view", room_slug=message_room_slug)


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


def user_new(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.info(request, "Uživatel vytvořen, nyní se můžete přihlásit.")
            return redirect("home")

    return render(request, "phorum/user_new.html", {
        'form': form
    })


@login_required
def user_edit(request):
    form = UserChangeForm(request.POST or None, request.FILES or None,
                          instance=request.user)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.info(request, "Profil uživatele upraven.")
            return redirect("user_edit")

    return render(request, "phorum/user_edit.html", {
        'form': form
    })
