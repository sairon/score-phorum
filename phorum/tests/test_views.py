# coding=utf-8
import os
from datetime import datetime

from autoslug.utils import slugify
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from user_sessions.utils.tests import Client

from .utils import new_public_thread, public_reply
from ..models import PrivateMessage, PublicMessage, Room, RoomVisit, User, UserRoomKeyring


class TestDataMixin(object):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            username='testclient1', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient1@example.com', is_staff=False, is_active=True
        )
        cls.user2 = User.objects.create(
            username='testclient2', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient2@example.com', is_staff=False, is_active=True
        )
        cls.user3 = User.objects.create(
            username='testclient3', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            email='testclient3@example.com', is_staff=False, is_active=True
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
