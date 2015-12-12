import datetime

import mock
from django.test import TestCase, override_settings
from django.utils.encoding import force_text

from ..forms import UserChangeForm
from ..models import User


class TestDataMixin(object):
    """
    Create test users. Taken from Django tests.
    """

    @classmethod
    def setUpTestData(cls):
        cls.u1 = User.objects.create(
            password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False, username='testclient',
            email='testclient@example.com', is_staff=False, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.u2 = User.objects.create(
            password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False, username='inactive',
            email='testclient2@example.com', is_staff=False, is_active=False,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.u3 = User.objects.create(
            password='sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161',
            last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False, username='staff',
            email='staffmember@example.com', is_staff=True, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.u4 = User.objects.create(
            password='', last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False,
            username='empty_password', email='empty_password@example.com',
            is_staff=False, is_active=True, date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.u5 = User.objects.create(
            password='$', last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False,
            username='unmanageable_password', email='unmanageable_password@example.com',
            is_staff=False, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )
        cls.u6 = User.objects.create(
            password='foo$bar', last_login=datetime.datetime(2006, 12, 17, 7, 3, 31), is_superuser=False,
            username='unknown_password', email='unknown_password@example.com',
            is_staff=False, is_active=True,
            date_joined=datetime.datetime(2006, 12, 17, 7, 3, 31)
        )


@override_settings(USE_TZ=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.SHA1PasswordHasher'])
class PasswordChangeFormTest(TestDataMixin, TestCase):
    def test_incorrect_password(self):
        user = User.objects.get(username='testclient')
        data = {
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
                'old_password': 'password',
                'new_password1': 'abc123',
                'new_password2': '',
            },
            {
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
            'old_password': 'password',
            'new_password1': 'abc123',
            'new_password2': 'abc123',
        }
        form = UserChangeForm(data, instance=user)
        self.assertTrue(form.is_valid())

    @mock.patch("django.contrib.auth.models.AbstractBaseUser.set_password")
    def test_password_changed_if_set_password(self, set_password):
        user = User.objects.get(username='testclient')
        data = {
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
            'motto': 'new motto',
        }
        form = UserChangeForm(data, instance=user)
        form.save()
        self.assertEqual(set_password.call_count, 0)
