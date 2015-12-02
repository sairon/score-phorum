# coding=utf-8
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import (
    LoginForm, PrivateMessageForm, PublicMessageForm, RoomCreationForm, RoomChangeForm,
    RoomPasswordPrompt, UserCreationForm, UserChangeForm
)
from .models import PrivateMessage, PublicMessage, Room, RoomVisit
from .utils import user_can_view_protected_room, get_ip_addr


def room_view(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    if room.protected:
        if not request.user.is_authenticated():
            messages.error(request, "Do zaheslovaných místností mají přístup pouze přihlášení uživatelé.")
            return redirect("home")
        elif not user_can_view_protected_room(request.user, room):
            return redirect("room_password_prompt", room_slug=room_slug)

    page_number = request.GET.get("page", 1)

    threads = PublicMessage.objects\
        .filter(room=room, thread=None) \
        .order_by("-last_reply") \
        .prefetch_related("author", "children__author", "children__recipient")

    paginator = Paginator(threads, 10)
    threads = paginator.page(page_number)

    last_visit_time = None
    if request.user.is_authenticated():
        visit, created = RoomVisit.objects.get_or_create(user=request.user, room=room)
        if not created:
            last_visit_time = visit.visit_time
            # just update the time
            visit.save()

    return render(request, "phorum/room_view.html", {
        'room': room,
        'threads': threads,
        'last_visit_time': last_visit_time,
        'message_form': PublicMessageForm(request.POST or None),
        'login_form': LoginForm(),
    })


@login_required
def room_password_prompt(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    if room.protected and not user_can_view_protected_room(request.user, room):
        messages.error(request, "Do místnosti, do které zasíláte zprávu, již nemáte přístup.")
        return redirect("home")

    form = RoomPasswordPrompt(request.POST or None, user=request.user, room=room)
    if form.is_valid():
        return redirect("room_view", room_slug=room_slug)

    return render(request, "phorum/room_password_prompt.html", {
        'room': room,
        'form': form,
    })


@login_required
def room_new(request):
    form = RoomCreationForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            room = form.save(author=request.user)
            return redirect("room_view", room_slug=room.slug)

    return render(request, "phorum/room_new.html", {
        'form': form,
    })


@login_required
def room_edit(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)
    form = RoomChangeForm(request.POST or None, instance=room)

    if request.method == "POST":
        if form.is_valid():
            room = form.save()
            return redirect("room_view", room_slug=room.slug)

    return render(request, "phorum/room_edit.html", {
        'room': room,
        'form': form,
    })


@login_required
def inbox(request):
    page_number = request.GET.get("page", 1)

    threads = PrivateMessage.objects\
        .filter(thread=None) \
        .filter(Q(author=request.user) | Q(recipient=request.user)) \
        .order_by("-last_reply") \
        .prefetch_related("author", "children__author", "children__recipient")

    paginator = Paginator(threads, 10)
    threads = paginator.page(page_number)

    last_visit_time = request.user.inbox_visit_time
    request.user.update_inbox_visit_time()

    return render(request, "phorum/inbox.html", {
        'threads': threads,
        'last_visit_time': last_visit_time,
        'message_form': PrivateMessageForm(request.POST or None),
    })


@require_POST
def inbox_send(request):
    message_form = PrivateMessageForm(request.POST or None)

    if request.user.is_authenticated():
        if message_form.is_valid():
            message_form.save(author=request.user)
            return redirect("inbox")
        else:
            messages.error(request, "Formulář se zprávou obsahuje chyby.")
    else:
        messages.error(request, "Pro zasílání zpráv musíte být přihlášen.")

    return inbox(request)


@require_POST
def message_send(request, room_slug):
    message_form = PublicMessageForm(request.POST or None)
    room = get_object_or_404(Room, slug=room_slug)

    if request.user.is_authenticated():
        if message_form.is_valid():
            message_form.save(author=request.user, room=room)
            return redirect("room_view", room_slug=room.slug)
        else:
            messages.error(request, "Formulář se zprávou obsahuje chyby.")
    else:
        messages.error(request, "Pro zasílání zpráv musíte být přihlášen.")

    return room_view(request, room_slug)


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


@login_required
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
            request.user.last_ip = get_ip_addr(request)
            request.user.save(update_fields=['last_ip'])
        else:
            user = form.get_user()
            if user and not user.is_active:
                messages.info(request, "Uživatelský účet není aktivní.")
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
            messages.info(request, "Uživatelský účet vytvořen, vyčkejte prosím na jeho aktivaci administrátorem.")
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
