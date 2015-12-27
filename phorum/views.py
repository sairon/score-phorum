# coding=utf-8
from copy import copy
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Count, Max, Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.http import is_safe_url
from django.utils.timezone import now
from django.views.decorators.cache import cache_control
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from user_sessions.models import Session

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
        .prefetch_related("author", "children__author", "children__recipient", "room", "children__room")

    max_threads = request.user.max_thread_roots if request.user.is_authenticated() else 10

    paginator = Paginator(threads, max_threads)
    threads = paginator.page(page_number)

    for thread in threads:
        thread.child_messages = list(thread.children.all())
        thread.last_child = thread.child_messages[-1] if len(thread.child_messages) else None

    last_visit_time = None
    new_posts = None
    if request.user.is_authenticated():
        # activity tracking - update last room
        request.session['last_action'] = {
            'name': room.name,
            'url': request.path,
        }

        visit, created = RoomVisit.objects.get_or_create(user=request.user, room=room)
        if not created:
            new_posts = PublicMessage.objects.filter(room=room, created__gte=visit.visit_time).count()
            last_visit_time = visit.visit_time
            # just update the time
            visit.save()
        else:
            new_posts = PublicMessage.objects.filter(room=room).count()

    return render(request, "phorum/room_view.html", {
        'room': room,
        'new_posts': new_posts,
        'threads': threads,
        'last_visit_time': last_visit_time,
        'message_form': PublicMessageForm(request.POST or None, author=request.user),
        'login_form': LoginForm(),
    })


@sensitive_post_parameters("password")
@login_required
def room_password_prompt(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    form = RoomPasswordPrompt(request.POST or None, user=request.user, room=room)
    if form.is_valid():
        return redirect("room_view", room_slug=room_slug)

    return render(request, "phorum/room_password_prompt.html", {
        'room': room,
        'form': form,
    })


@sensitive_post_parameters("password")
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


@sensitive_post_parameters("password")
@login_required
def room_edit(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    if not room.can_be_modified_by(request.user):
        return HttpResponseForbidden("Nemáte oprávnění editovat tuto místnost.")

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
def room_mark_unread(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    if room.protected:
        if not user_can_view_protected_room(request.user, room):
            return redirect("room_password_prompt", room_slug=room_slug)

    to_delete = RoomVisit.objects.filter(user=request.user, room=room)
    if to_delete.count():
        to_delete.delete()
        messages.info(request, u"Místnost \"{}\" byla označena jako nepřečtená.".format(room.name))

    return redirect("home")


@login_required
def inbox(request):
    page_number = request.GET.get("page", 1)

    threads = PrivateMessage.objects\
        .filter(thread=None) \
        .filter(Q(author=request.user) | Q(recipient=request.user)) \
        .order_by("-last_reply") \
        .prefetch_related("author", "children__author", "children__recipient")

    paginator = Paginator(threads, request.user.max_thread_roots)
    threads = paginator.page(page_number)

    for thread in threads:
        thread.child_messages = list(thread.children.all())
        thread.last_child = thread.child_messages[-1] if len(thread.child_messages) else None

    # RequestContext gets instantiated here
    response = render(request, "phorum/inbox.html", {
        'threads': threads,
        'last_visit_time': request.user.inbox_visit_time,
        'message_form': PrivateMessageForm(request.POST or None, author=request.user),
    })

    # update inbox visit time after getting count of new inbox messages
    # in inbox_messages context processor
    request.user.update_inbox_visit_time()

    return response


@require_POST
@login_required
def inbox_send(request):
    message_form = PrivateMessageForm(request.POST or None, author=request.user)

    if message_form.is_valid():
        message_form.save()
        return redirect("inbox")
    else:
        messages.error(request, "Formulář se zprávou obsahuje chyby.")

    return inbox(request)


@require_POST
@login_required
def message_send(request, room_slug):
    message_form = PublicMessageForm(request.POST or None, author=request.user)
    room = get_object_or_404(Room, slug=room_slug)

    if room.protected and not user_can_view_protected_room(request.user, room):
        messages.error(request, "Do místnosti, do které zasíláte zprávu, již nemáte přístup.")
        return redirect("home")

    if message_form.is_valid():
        if message_form.cleaned_data['to_inbox']:
            if "thread" in request.POST:
                request.POST = copy(request.POST)
                del request.POST['thread']
            return inbox_send(request)
        message_form.save(room=room)
        request.user.increase_kredyti()
        return redirect("room_view", room_slug=room.slug)
    else:
        messages.error(request, "Formulář se zprávou obsahuje chyby.")

    return room_view(request, room_slug)


@cache_control(no_cache=True, must_revalidate=True, no_store=True, max_age=0)
def room_list(request):
    rooms = Room.objects.annotate(total_messages=Count("publicmessage"),
                                  last_message_time=Max("publicmessage__created"))

    visits = RoomVisit.objects.visits_for_user(request.user) if request.user.is_authenticated() else None

    return render(request, "phorum/room_list.html", {
        'rooms': rooms,
        'login_form': LoginForm(),
        'visits': visits,
        'next': request.POST.get("next", request.GET.get("next", "")),
    })


@login_required
def message_delete(request, message_id):
    is_private = request.GET.get("inbox", 0) == "1"
    message = get_object_or_404(PrivateMessage if is_private else PublicMessage, pk=message_id)

    if message.can_be_deleted_by(request.user):
        if not is_private:
            kredyti_penalty = 1 if request.user == message.author else 5
            message.author.decrease_kredyti(kredyti_penalty)
        message.delete()
        messages.info(request, "Zpráva byla smazána.")
    else:
        messages.error(request, "Nemáte oprávnění ke smazání zprávy.")

    if is_private:
        return redirect("inbox")

    message_room_slug = message.room.slug
    return redirect("room_view", room_slug=message_room_slug)


@sensitive_post_parameters()
def login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            request.user.last_ip = get_ip_addr(request)
            request.user.save(update_fields=['last_ip'])
            redirect_to = request.POST.get("next",
                                           request.GET.get("next", ""))
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = reverse("home")
            return HttpResponseRedirect(redirect_to)
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


@sensitive_post_parameters("password1", "password2")
def user_new(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.info(request, "Uživatelský účet vytvořen, nyní se můžete přihlásit.")
            return redirect("home")

    return render(request, "phorum/user_new.html", {
        'form': form
    })


@sensitive_post_parameters("old_password", "new_password1", "new_password2")
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


@login_required
def users(request):
    active_threshold = now() - timedelta(minutes=settings.ACTIVE_USERS_TIMEOUT)

    sessions = Session.objects\
        .filter(user__isnull=False, expire_date__gte=now(), last_activity__gte=active_threshold)\
        .prefetch_related('user')\
        .order_by('user__username')\
        .distinct('user__username')

    return render(request, "phorum/users.html", {
        'sessions': sessions
    })
