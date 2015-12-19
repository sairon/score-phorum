# coding=utf-8
from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from user_sessions.utils.tests import Client

from .utils import new_public_thread, public_reply
from ..models import PrivateMessage, Room, User


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
