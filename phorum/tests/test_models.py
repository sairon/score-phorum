from django.test import TestCase, override_settings

from ..models import PublicMessage, Room, User


class TestDataMixin(object):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
                username='testclient1', password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
                email='testclient1@example.com', is_staff=False, is_active=True
        )
        cls.room = Room.objects.create(
                name="room", pinned=False
        )


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class TestModels(TestDataMixin, TestCase):
    def test_message_breaking(self):
        entered_text = "hello\nworld"
        expected_text = "hello<br>world"
        message = PublicMessage.objects.create(room=self.room, author=self.user1, text=entered_text)
        self.assertEqual(PublicMessage.objects.get(id=message.id).text, expected_text)

    def test_message_stripping(self):
        entered_text = "     \t\r\n    hello      \t\r\n    "
        expected_text = "hello"
        message = PublicMessage.objects.create(room=self.room, author=self.user1, text=entered_text)
        self.assertEqual(PublicMessage.objects.get(id=message.id).text, expected_text)
