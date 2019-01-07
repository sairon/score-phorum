import datetime

import mock
from django.test import TestCase, override_settings
from django.utils.encoding import force_text

from ..forms import PrivateMessageForm, UserChangeForm
from ..models import PrivateMessage, User


class TestDataMixin(object):
    """
    Create test users. Taken from Django tests.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False, username='testclient',
            email='testclient@example.com', is_staff=False, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.user2 = User.objects.create(
            password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False, username='testclient2',
            email='testclient2@example.com', is_staff=False, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.user3 = User.objects.create(
            password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False, username='testclient3',
            email='testclient3@example.com', is_staff=False, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class PrivateMessageFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.u1_to_u2 = PrivateMessage.objects.create(
            author=self.user1, recipient=self.user2,
            text="message"
        )

    def test_success_new_thread(self):
        data = {
            'thread': "",
            'text': "new thread",
            'recipient': self.user2
        }
        form = PrivateMessageForm(data, author=self.user1)
        self.assertTrue(form.is_valid(), form.errors)

    def test_success_reply(self):
        data = {
            'thread': self.u1_to_u2.id,
            'text': "reply",
            'recipient': self.user1
        }
        form = PrivateMessageForm(data, author=self.user2)
        self.assertTrue(form.is_valid(), form.errors)

    def test_success_reply_self(self):
        data = {
            'thread': self.u1_to_u2.id,
            'text': "reply",
            'recipient': self.user1
        }
        form = PrivateMessageForm(data, author=self.user1)
        self.assertTrue(form.is_valid(), form.errors)

    def test_not_senders_thread(self):
        data = {
            'thread': self.u1_to_u2.id,
            'text': "hijack",
            'recipient': self.user1.id,
        }
        form = PrivateMessageForm(data, author=self.user3)
        self.assertFalse(form.is_valid())
        self.assertEqual(form['thread'].errors,
                         [force_text(form.error_messages['invalid_thread'])])


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class UserChangeFormTest(TestDataMixin, TestCase):
    def test_incorrect_password(self):
        user = User.objects.get(username='testclient')
        data = {
            'max_thread_roots': '10',
            'old_password': 'test',
            'new_password1': 'abc123',
            'new_password2': 'abc123',
        }
        form = UserChangeForm(data, instance=user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form["old_password"].errors,
                         [force_text(form.error_messages['password_incorrect'])])

    def test_password_verification(self):
        # The two new passwords do not match.
        user = User.objects.get(username='testclient')
        data = {
            'max_thread_roots': '10',
            'old_password': 'password',
            'new_password1': 'abc123',
            'new_password2': 'abc',
        }
        form = UserChangeForm(data, instance=user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form["new_password2"].errors,
                         [force_text(form.error_messages['password_mismatch'])])

    def test_password_verification_empty(self):
        # The two new passwords do not match.
        user = User.objects.get(username='testclient')
        data_variations = [
            {
                'max_thread_roots': '10',
                'old_password': 'password',
                'new_password1': 'abc123',
                'new_password2': '',
            },
            {
                'max_thread_roots': '10',
                'old_password': 'password',
                'new_password1': '',
                'new_password2': 'abc123',
            }
        ]
        for data in data_variations:
            form = UserChangeForm(data, instance=user)
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors['__all__'],
                             [force_text(form.error_messages['password_mismatch'])])

    def test_password_required(self):
        user = User.objects.get(username='testclient')
        data = {
            'max_thread_roots': '10',
            'old_password': '',
            'new_password1': 'abc123',
            'new_password2': 'abc123',
        }
        form = UserChangeForm(data, instance=user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'],
                         [force_text(form.error_messages['password_incorrect'])])

    def test_success(self):
        # The success case.
        user = User.objects.get(username='testclient')
        data = {
            'max_thread_roots': '10',
            'old_password': 'password',
            'new_password1': 'abc123',
            'new_password2': 'abc123',
        }
        form = UserChangeForm(data, instance=user)
        self.assertTrue(form.is_valid(), form.errors)

    @mock.patch("django.contrib.auth.models.AbstractBaseUser.set_password")
    def test_password_changed_if_set_password(self, set_password):
        user = User.objects.get(username='testclient')
        data = {
            'max_thread_roots': '10',
            'old_password': 'password',
            'new_password1': 'abc123',
            'new_password2': 'abc123',
        }
        form = UserChangeForm(data, instance=user)
        form.save()
        self.assertEqual(set_password.call_count, 1)

    @mock.patch("django.contrib.auth.models.AbstractBaseUser.set_password")
    def test_password_unchanged_if_not_set_password(self, set_password):
        user = User.objects.get(username='testclient')
        data = {
            'max_thread_roots': '10',
            'motto': 'new motto',
        }
        form = UserChangeForm(data, instance=user)
        form.save()
        self.assertEqual(set_password.call_count, 0)
