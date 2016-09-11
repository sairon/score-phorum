# coding=utf-8
import os
import random
import string
from datetime import datetime

import mock
from autoslug.utils import slugify
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.test import TestCase, override_settings
from user_sessions.utils.tests import Client

from phorum.models.utils import make_resource_upload_path, css_upload_path, js_upload_path
from phorum.utils import get_custom_resource_filename
from .utils import new_public_thread, public_reply
from ..models import PrivateMessage, PublicMessage, Room, RoomVisit, User, UserRoomKeyring, customization_storage, \
    UserCustomization


class TestDataMixin(object):
    @classmethod
    def setUpTestData(cls):
        # Green ribbon
        cls.user1 = User.objects.create(
            username='testclient1', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient1@example.com', is_staff=False, is_active=True,
            kredyti=0
        )
        assert cls.user1.level == User.LEVEL_GREEN
        # Maroon ribbon
        cls.user2 = User.objects.create(
            username='testclient2', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient2@example.com', is_staff=False, is_active=True,
            kredyti=3100
        )
        assert cls.user2.level == User.LEVEL_MAROON
        # One dot
        cls.user3 = User.objects.create(
            username='testclient3', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient3@example.com', is_staff=False, is_active=True,
            kredyti=6100
        )
        assert cls.user3.level == User.LEVEL_1_DOT
        # God
        cls.user4 = User.objects.create(
            username='testclient4', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient3@example.com', is_staff=False, is_active=True,
            kredyti=36000
        )
        assert cls.user4.level == User.LEVEL_GOD
        # admin
        cls.user_admin = User.objects.create(
            username='the_admin', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='the_admin@example.com', is_staff=False, is_active=True,
            kredyti=1, level_override=User.LEVEL_ADMIN
        )
        cls.user_inactive = User.objects.create(
            username='inactive', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='inactive@example.com', is_staff=False, is_active=False
        )
        cls.rooms = {
            'pinned1': Room.objects.create(
                    name="room1 pinned", pinned=True
            ),
            'unpinned1': Room.objects.create(
                    name="room1 unpinned", pinned=False
            ),
            'unpinned2': Room.objects.create(
                    name="room2 unpinned", pinned=False
            ),
            'protected': Room.objects.create(
                    name="room3 protected", password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
                    password_changed=datetime.now()
            )
        }


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class RoomListTest(TestDataMixin, TestCase):
    client_class = Client

    def test_rooms_present(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context['rooms'].count(), len(self.rooms))
        self.assertEqual(response.status_code, 200)
        for text in (x.name for x in self.rooms.values()):
            self.assertContains(response, text)

    def test_login_form_present(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'value="Login"')

    def test_authenticated_login_form_not_present(self):
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, 'value="Login"')

    def test_unread_count_all(self):
        message1 = new_public_thread(self.rooms['pinned1'], self.user1)
        public_reply(message1, self.user2)
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("home"))
        self.assertRegexpMatches(response.content, r'<span class="post-count">\s*2\s*</span>')

    def test_unread_count_resets(self):
        message1 = new_public_thread(self.rooms['pinned1'], self.user1)
        public_reply(message1, self.user2)
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("home"))
        self.assertRegexpMatches(response.content, r'<span class="post-count">\s*2\s*</span>')
        # visit room to reset counter
        self.client.get(reverse("room_view", kwargs={'room_slug': self.rooms['pinned1'].slug}))
        # check home again
        response = self.client.get(reverse("home"))
        self.assertRegexpMatches(response.content, r'<span class="post-count">\s*0/2\s*</span>')

    def test_unread_count_increases(self):
        message1 = new_public_thread(self.rooms['pinned1'], self.user1)
        public_reply(message1, self.user2)
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("home"))
        self.assertRegexpMatches(response.content, r'<span class="post-count">\s*2\s*</span>')
        # visit room to reset counter
        self.client.get(reverse("room_view", kwargs={'room_slug': self.rooms['pinned1'].slug}))
        # send new reply
        public_reply(message1, self.user2)
        # check home again
        response = self.client.get(reverse("home"))
        self.assertRegexpMatches(response.content, r'<span class="post-count">\s*1/3\s*</span>')


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class RoomViewTest(TestDataMixin, TestCase):
    client_class = Client

    def test_protected_kicks_unauthenticated(self):
        response = self.client.get(reverse("room_view", kwargs={'room_slug': self.rooms['protected'].slug}))
        self.assertRedirects(response, reverse("home"))

    def test_protected_password_prompt(self):
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("room_view", kwargs={'room_slug': self.rooms['protected'].slug}))
        self.assertRedirects(response, reverse("room_password_prompt", kwargs={'room_slug': self.rooms['protected'].slug}))

    def test_password_prompt_accepts_valid(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'password': "password",
        }
        response = self.client.post(reverse("room_password_prompt", kwargs={'room_slug': self.rooms['protected'].slug}),
                                    data)
        self.assertRedirects(response, reverse("room_view", kwargs={'room_slug': self.rooms['protected'].slug}))

    def test_password_prompt_rejects_invalid(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'password': "le_password",
        }
        prompt_url = reverse("room_password_prompt", kwargs={'room_slug': self.rooms['protected'].slug})
        response = self.client.post(prompt_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        # test that the user really can't access the room
        response = self.client.get(reverse("room_view", kwargs={'room_slug': self.rooms['protected'].slug}))
        self.assertRedirects(response, prompt_url)

    def test_authenticated_can_create_thread(self):
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        data = {
            'recipient': "",
            'thread': "",
            'text': "text",
        }
        response = self.client.post(reverse("message_send", kwargs=room_kwargs),
                                    data)
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs))
        self.assertEqual(PublicMessage.objects.count(), 1)

    def test_authenticated_can_create_thread_with_recipient(self):
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        data = {
            'recipient': self.user2.username,
            'thread': "",
            'text': "text",
        }
        response = self.client.post(reverse("message_send", kwargs=room_kwargs),
                                    data)
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs))
        self.assertEqual(PublicMessage.objects.count(), 1)

    def test_authenticated_can_reply_thread(self):
        thread = new_public_thread(self.rooms['unpinned1'], self.user2)
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        data = {
            'recipient': self.user2.username,
            'thread': thread.id,
            'text': "text"
        }
        response = self.client.post(reverse("message_send", kwargs=room_kwargs),
                                    data)
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs))
        self.assertEqual(PublicMessage.objects.count(), 2)

    def test_unauthenticated_can_not_post(self):
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        data = {
            'recipient': "",
            'thread': "",
            'text': "text",
        }
        send_url = reverse("message_send", kwargs=room_kwargs)
        response = self.client.post(send_url, data)
        self.assertRedirects(response, "%s?next=%s" % (reverse("home"), send_url))
        self.assertEqual(PublicMessage.objects.count(), 0)

    def test_can_not_post_to_protected(self):
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['protected'].slug}
        data = {
            'recipient': "",
            'thread': "",
            'text': "text",
        }
        send_url = reverse("message_send", kwargs=room_kwargs)
        response = self.client.post(send_url, data)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Do místnosti, do které zasíláte zprávu, již nemáte přístup")
        self.assertEqual(PublicMessage.objects.count(), 0)

    def test_can_post_to_allowed_protected(self):
        assert self.client.login(username="testclient1", password="password")
        UserRoomKeyring.objects.create(room=self.rooms['protected'], user=self.user1)
        room_kwargs = {'room_slug': self.rooms['protected'].slug}
        data = {
            'recipient': "",
            'thread': "",
            'text': "text",
        }
        response = self.client.post(reverse("message_send", kwargs=room_kwargs),
                                    data)
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs))
        self.assertEqual(PublicMessage.objects.count(), 1)

    def test_send_reply_to_inbox(self):
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        data = {
            'recipient': self.user2.username,
            'thread': "",
            'text': "text",
            'to_inbox': 1,
        }
        response = self.client.post(reverse("message_send", kwargs=room_kwargs),
                                    data)
        self.assertRedirects(response, reverse("inbox"))
        self.assertEqual(PrivateMessage.objects.filter(recipient=self.user2).count(), 1)

    def test_send_reply_to_inbox_without_recipient_fails(self):
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        data = {
            'recipient': "",
            'thread': "",
            'text': "text",
            'to_inbox': 1,
        }
        response = self.client.post(reverse("message_send", kwargs=room_kwargs),
                                    data)
        self.assertContains(response, "Formulář se zprávou obsahuje chyby")
        self.assertEqual(PrivateMessage.objects.filter(recipient=self.user2).count(), 0)

    def test_can_delete_own_messages(self):
        thread = new_public_thread(self.rooms['unpinned1'], self.user1)
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        response = self.client.get(reverse("message_delete", kwargs={'message_id': thread.id}))
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs),
                             fetch_redirect_response=False)
        response = self.client.get(reverse("room_view", kwargs=room_kwargs))
        self.assertContains(response, "Zpráva byla smazána")
        self.assertEqual(PublicMessage.objects.count(), 0)

    def test_can_not_delete_others_messages(self):
        thread = new_public_thread(self.rooms['unpinned1'], self.user2)
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        response = self.client.get(reverse("message_delete", kwargs={'message_id': thread.id}))
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs),
                             fetch_redirect_response=False)
        response = self.client.get(reverse("room_view", kwargs=room_kwargs))
        self.assertContains(response, "Nemáte oprávnění ke smazání zprávy")
        self.assertEqual(PublicMessage.objects.count(), 1)

    def test_god_can_delete_maroon(self):
        thread = new_public_thread(self.rooms['unpinned1'], self.user2)
        assert self.client.login(username="testclient4", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        response = self.client.get(reverse("message_delete", kwargs={'message_id': thread.id}))
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs),
                             fetch_redirect_response=False)
        response = self.client.get(reverse("room_view", kwargs=room_kwargs))
        self.assertContains(response, "Zpráva byla smazána")
        self.assertEqual(PublicMessage.objects.count(), 0)

    def test_god_can_not_delete_dot(self):
        thread = new_public_thread(self.rooms['unpinned1'], self.user3)
        assert self.client.login(username="testclient4", password="password")
        room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
        response = self.client.get(reverse("message_delete", kwargs={'message_id': thread.id}))
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs),
                             fetch_redirect_response=False)
        response = self.client.get(reverse("room_view", kwargs=room_kwargs))
        self.assertContains(response, "Nemáte oprávnění ke smazání zprávy")
        self.assertEqual(PublicMessage.objects.count(), 1)

    def test_admin_can_delete_everything(self):
        for user in (self.user1, self.user2, self.user3, self.user4, self.user_admin):
            thread = new_public_thread(self.rooms['unpinned1'], user)
            assert self.client.login(username="the_admin", password="password")
            room_kwargs = {'room_slug': self.rooms['unpinned1'].slug}
            response = self.client.get(reverse("message_delete", kwargs={'message_id': thread.id}))
            self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs),
                                 fetch_redirect_response=False)
            response = self.client.get(reverse("room_view", kwargs=room_kwargs))
            self.assertContains(response, "Zpráva byla smazána")
            self.assertEqual(PublicMessage.objects.count(), 0)

    def test_room_author_can_delete_others_messages(self):
        room = Room.objects.create(
            name="new room",
            author=self.user1,
        )
        thread = new_public_thread(room, self.user2)
        assert self.client.login(username="testclient1", password="password")
        room_kwargs = {'room_slug': room.slug}
        response = self.client.get(reverse("message_delete", kwargs={'message_id': thread.id}))
        self.assertRedirects(response, reverse("room_view", kwargs=room_kwargs),
                             fetch_redirect_response=False)
        response = self.client.get(reverse("room_view", kwargs=room_kwargs))
        self.assertContains(response, "Zpráva byla smazána")
        self.assertEqual(PublicMessage.objects.count(), 0)

    def test_author_can_edit_room(self):
        room = Room.objects.create(
            name="new room",
            author=self.user1,
        )
        room.set_password("password")
        room.save()
        assert self.client.login(username="testclient1", password="password")
        data = {
            'password': "",
            'clear_password': "1",
        }
        response = self.client.post(reverse("room_edit", kwargs={'room_slug': room.slug}), data)
        self.assertRedirects(response, reverse("room_view", kwargs={'room_slug': room.slug}))

    def test_moderator_can_not_edit_room(self):
        room = Room.objects.create(
            name="new room",
            author=self.user2,
            moderator=self.user1,
        )
        room.set_password("password")
        room.save()
        assert self.client.login(username="testclient1", password="password")
        data = {
            'password': "",
            'clear_password': "1",
        }
        response = self.client.post(reverse("room_edit", kwargs={'room_slug': room.slug}), data)
        self.assertEqual(response.status_code, 403)

    def test_others_can_not_edit_room(self):
        room = Room.objects.create(
            name="new room",
            author=self.user1,
            moderator=self.user2,
        )
        room.set_password("password")
        room.save()
        assert self.client.login(username="testclient3", password="password")
        data = {
            'password': "",
            'clear_password': "1",
        }
        response = self.client.post(reverse("room_edit", kwargs={'room_slug': room.slug}), data)
        self.assertEqual(response.status_code, 403)

    def test_password_change_invalidates_access(self):
        room = Room.objects.create(
            name="new room",
            author=self.user1,
        )
        room.set_password("password")
        room.save()
        assert self.client.login(username="testclient1", password="password")
        # redirects to the prompt if not in the keyring
        response = self.client.get(reverse("room_view", kwargs={'room_slug': room.slug}))
        self.assertRedirects(response, reverse("room_password_prompt", kwargs={'room_slug': room.slug}))
        UserRoomKeyring.objects.create(user=self.user1, room=room)
        # allowed if it's in the keyring
        response = self.client.get(reverse("room_view", kwargs={'room_slug': room.slug}))
        self.assertEqual(response.status_code, 200)
        data = {
            'password': "new_password",
        }
        response = self.client.post(reverse("room_edit", kwargs={'room_slug': room.slug}), data)
        # should be redirected to the password prompt after changing the password
        self.assertRedirects(response, reverse("room_view", kwargs={'room_slug': room.slug}),
                             fetch_redirect_response=False)
        response = self.client.get(reverse("room_view", kwargs={'room_slug': room.slug}))
        self.assertRedirects(response, reverse("room_password_prompt", kwargs={'room_slug': room.slug}))

    def test_room_creation(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'name': "new room",
            'password': "",
            'moderator': ""
        }
        room_slug = slugify(data['name'])
        response = self.client.post(reverse("room_new"), data)
        self.assertRedirects(response, reverse("room_view", kwargs={'room_slug': room_slug}))
        self.assertEqual(Room.objects.filter(name="new room", pinned=False).count(), 1)

    def test_protected_room_creation(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'name': "new room",
            'password': "password",
            'moderator': ""
        }
        room_slug = slugify(data['name'])
        response = self.client.post(reverse("room_new"), data)
        self.assertRedirects(response, reverse("room_view", kwargs={'room_slug': room_slug}),
                             fetch_redirect_response=False)
        self.assertEqual(Room.objects.filter(name="new room").count(), 1)
        response = self.client.get(reverse("room_view", kwargs={'room_slug': room_slug}))
        self.assertRedirects(response, reverse("room_password_prompt", kwargs={'room_slug': room_slug}))

    def test_mark_unread(self):
        assert self.client.login(username="testclient1", password="password")
        room = self.rooms['unpinned1']
        self.client.get(reverse("room_view", kwargs={'room_slug': room.slug}))
        self.assertEqual(RoomVisit.objects.filter(room=room, user=self.user1).count(), 1)
        response = self.client.get(reverse("room_mark_unread", kwargs={'room_slug': room.slug}))
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"))
        self.assertEqual(RoomVisit.objects.filter(room=room, user=self.user1).count(), 0)
        self.assertContains(response,  "byla označena jako nepřečtená")

    def test_mark_unread_nonvisited(self):
        assert self.client.login(username="testclient1", password="password")
        room = self.rooms['unpinned1']
        response = self.client.get(reverse("room_mark_unread", kwargs={'room_slug': room.slug}),)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "byla označena jako nepřečtená")
        self.assertEqual(RoomVisit.objects.filter(room=room, user=self.user1).count(), 0)


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class InboxText(TestDataMixin, TestCase):
    client_class = Client

    def _create_test_messages(self):
        thread = PrivateMessage.objects.create(
            author=self.user1, recipient=self.user2,
            text="%new_thread%"
        )
        reply = PrivateMessage.objects.create(
            author=self.user2, recipient=self.user1,
            text="%new_thread_reply%", thread=thread
        )
        return thread, reply

    def test_inbox_messages_present(self):
        thread, reply = self._create_test_messages()
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("inbox"))
        self.assertContains(response, thread.text)
        self.assertContains(response, reply.text)

    def test_inbox_unread_count(self):
        self._create_test_messages()
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("home"))
        self.assertContains(response, '<span class="inbox-new-messages">2</span>')
        response = self.client.get(reverse("inbox"))
        self.assertContains(response, '<span class="inbox-new-messages">2</span>',
                            msg_prefix="new messages count reset in the first visit of inbox")

    def test_inbox_unread_count_resets(self):
        self._create_test_messages()
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("home"))
        self.assertContains(response, '<span class="inbox-new-messages">2</span>')
        # visit inbox - reset should occur
        self.client.get(reverse("inbox"))
        # check homepage again
        response = self.client.get(reverse("home"))
        self.assertContains(response, '<span class="inbox-new-messages">0</span>')

    def test_can_send_message(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'recipient': self.user2.username,
            'thread': "",
            'text': "text"
        }
        response = self.client.post(reverse("inbox_send"), data)
        self.assertRedirects(response, reverse("inbox"))

    def test_can_reply_message(self):
        thread, reply = self._create_test_messages()
        assert self.client.login(username="testclient1", password="password")
        data = {
            'recipient': self.user2.username,
            'thread': thread.id,
            'text': "%posted_reply%"
        }
        response = self.client.post(reverse("inbox_send"), data)
        self.assertRedirects(response, reverse("inbox"), fetch_redirect_response=False)
        response = self.client.get(reverse("inbox"))
        self.assertContains(response, data['text'])

    def test_form_validation_message(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'recipient': self.user2.username,
            'thread': "invalid",
            'text': "%posted_reply%"
        }
        response = self.client.post(reverse("inbox_send"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formulář se zprávou obsahuje chyby")

    def test_can_delete_own_messages(self):
        thread, reply = self._create_test_messages()
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("message_delete",
                                           kwargs={'message_id': thread.id}),
                                   {'inbox': "1"})
        self.assertRedirects(response, reverse("inbox"), fetch_redirect_response=False)
        response = self.client.get(reverse("inbox"))
        self.assertContains(response, "Zpráva byla smazána")

    def test_can_delete_received_messages(self):
        thread, reply = self._create_test_messages()
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("message_delete",
                                           kwargs={'message_id': reply.id}),
                                   {'inbox': "1"})
        self.assertRedirects(response, reverse("inbox"), fetch_redirect_response=False)
        response = self.client.get(reverse("inbox"))
        self.assertContains(response, "Zpráva byla smazána")

    def test_can_not_see_others_messages(self):
        thread = PrivateMessage.objects.create(
            author=self.user3, recipient=self.user2,
            text="%new_thread%"
        )
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("inbox"))
        self.assertNotContains(response, thread.text)

    def test_can_not_reply_others_messages(self):
        thread = PrivateMessage.objects.create(
            author=self.user3, recipient=self.user2,
            text="%new_thread%"
        )
        assert self.client.login(username="testclient1", password="password")
        data = {
            'recipient': self.user2.username,
            'thread': thread.id,
            'text': "%posted_reply%"
        }
        response = self.client.post(reverse("inbox_send"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formulář se zprávou obsahuje chyby")

    def test_can_not_delete_others_messages(self):
        thread = PrivateMessage.objects.create(
            author=self.user3, recipient=self.user2,
            text="%new_thread%"
        )
        assert self.client.login(username="testclient1", password="password")
        response = self.client.get(reverse("message_delete",
                                           kwargs={'message_id': thread.id}),
                                   {'inbox': "1"})
        self.assertRedirects(response, reverse("inbox"), fetch_redirect_response=False)
        response = self.client.get(reverse("inbox"))
        self.assertContains(response, "Nemáte oprávnění ke smazání zprávy")


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class AuthenticationTest(TestDataMixin, TestCase):
    client_class = Client

    def test_login(self):
        data = {
            'username': "testclient1",
            'password': "password"
        }
        response = self.client.post(reverse("login"), data)
        self.assertRedirects(response, reverse("home"))
        self.assertIn(settings.SESSION_COOKIE_NAME, self.client.cookies)
        self.assertIn(SESSION_KEY, self.client.session)

    def test_logout(self):
        assert self.client.login(username="testclient1", password="password")
        self.assertIn(SESSION_KEY, self.client.session)
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=True)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_inactive_can_not_login(self):
        data = {
            'username': "inactive",
            'password': "password"
        }
        response = self.client.post(reverse("login"), data)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Uživatelský účet není aktivní")
        self.assertNotIn(settings.SESSION_COOKIE_NAME, self.client.cookies)

    def test_invalid_login(self):
        data = {
            'username': "testclient1",
            'password': "invalid"
        }
        response = self.client.post(reverse("login"), data)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Neplatný login nebo heslo")
        self.assertNotIn(settings.SESSION_COOKIE_NAME, self.client.cookies)


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class UserManagementTest(TestDataMixin, TestCase):
    client_class = Client

    def setUp(self):
        os.environ['RECAPTCHA_TESTING'] = "True"

    def tearDown(self):
        del os.environ['RECAPTCHA_TESTING']

    def test_user_creation(self):
        data = {
            'username': "new_user",
            'password1': "password",
            'password2': "password",
            'motto': "user's motto",
            'email': "newemail@example.com",
            'g-recaptcha-response': "PASSED"
        }
        users_before = User.objects.count()
        response = self.client.post(reverse("user_new"), data)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Uživatelský účet vytvořen")
        self.assertEqual(User.objects.count(), users_before + 1)
        self.assertEqual(User.objects.filter(username=data['username'],
                                             motto=data['motto'],
                                             email=data['email']).count(),
                         1)

    def test_user_form_error(self):
        data = {
            'username': "new_user",
            'password1': "password",
            'password2': "",
            'motto': "user's motto",
            'email': "newemail@example.com",
            'g-recaptcha-response': "PASSED"
        }
        users_before = User.objects.count()
        response = self.client.post(reverse("user_new"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), users_before)

    def test_user_edit(self):
        assert self.client.login(username="testclient1", password="password")
        data = {
            'max_thread_roots': 10,
            'motto': "new motto"
        }
        response = self.client.post(reverse("user_edit"), data)
        self.assertRedirects(response, reverse("user_edit"), fetch_redirect_response=False)
        response = self.client.get(reverse("user_edit"))
        self.assertContains(response, "Profil uživatele upraven")

    def test_user_customization_create(self):
        assert self.client.login(username="testclient1", password="password")
        # Generate some random text
        custom_css = ''.join(random.choice(string.ascii_letters) for _ in range(60))
        custom_js = ''.join(random.choice(string.ascii_letters) for _ in range(60))
        data = {
            'custom_css': custom_css,
            'custom_js': custom_js
        }

        m = mock.mock_open()

        with mock.patch("os.open"), mock.patch("fcntl.flock"), mock.patch("os.close"), mock.patch("os.fdopen", m):
            response = self.client.post(reverse("user_customization"), data)
            handle = m()
            self.assertEqual(handle.write.call_args_list, [mock.call(custom_css), mock.call(custom_js)])
            self.assertRedirects(response, reverse("user_customization"), fetch_redirect_response=False)

    def test_user_customization_get(self):
        assert self.client.login(username="testclient1", password="password")
        customization_mock = mock.Mock()
        customization_mock.user = self.user1
        css_path = css_upload_path(customization_mock, "anything")
        js_path = js_upload_path(customization_mock, "anything")

        UserCustomization.objects.create(
            user=self.user1, custom_css=css_path, custom_js=js_path
        )

        with mock.patch("sendfile.sendfile") as sendfile:
            sendfile.return_value = HttpResponse()
            response = self.client.get(reverse("custom_resource", args=(self.user1.id, "js")))
            self.assertEqual(response.status_code, 200, response.content)
            sendfile.assert_called_once_with(response.wsgi_request,
                                             os.path.join(settings.SENDFILE_ROOT, js_path))

        with mock.patch("sendfile.sendfile") as sendfile:
            sendfile.return_value = HttpResponse()
            response = self.client.get(reverse("custom_resource", args=(self.user1.id, "css")))
            self.assertEqual(response.status_code, 200, response.content)
            sendfile.assert_called_once_with(response.wsgi_request,
                                             os.path.join(settings.SENDFILE_ROOT, css_path))

    def test_user_customization_delete(self):
        assert self.client.login(username="testclient1", password="password")
        customization_mock = mock.Mock()
        customization_mock.user = self.user1
        css_path = css_upload_path(customization_mock, "anything")
        js_path = js_upload_path(customization_mock, "anything")

        customization = UserCustomization.objects.create(
            user=self.user1, custom_css=css_path, custom_js=js_path
        )

        css_full_path = customization.custom_css.path
        js_full_path = customization.custom_js.path

        data = {
            'custom_css': "",
            'custom_js': ""
        }

        with mock.patch("django.core.files.storage.FileSystemStorage.delete") as delete:
            self.client.post(reverse("user_customization"), data)
            self.assertEqual(delete.call_count, 2)
            self.assertEqual(delete.call_args_list, [mock.call(css_full_path), mock.call(js_full_path)])

    def test_user_customization_acl(self):
        customization_mock = mock.Mock()
        customization_mock.user = self.user1
        css_path = css_upload_path(customization_mock, "anything")
        js_path = js_upload_path(customization_mock, "anything")

        UserCustomization.objects.create(
            user=self.user1, custom_css=css_path, custom_js=js_path
        )

        # First user should be able to get his resources.
        assert self.client.login(username="testclient1", password="password")
        with mock.patch("sendfile.sendfile") as sendfile:
            sendfile.return_value = HttpResponse()
            response = self.client.get(reverse("custom_resource", args=(self.user1.id, "css")))
            self.assertEqual(response.status_code, 200)
            response = self.client.get(reverse("custom_resource", args=(self.user1.id, "js")))
            self.assertEqual(response.status_code, 200)

        # Second user should not be able to get first user's resources.
        assert self.client.login(username="testclient2", password="password")
        with mock.patch("sendfile.sendfile") as sendfile:
            sendfile.return_value = HttpResponse()
            response = self.client.get(reverse("custom_resource", args=(self.user1.id, "css")))
            self.assertEqual(response.status_code, 403)
            response = self.client.get(reverse("custom_resource", args=(self.user1.id, "js")))
            self.assertEqual(response.status_code, 403)
