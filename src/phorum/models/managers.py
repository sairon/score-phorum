from django.contrib.auth.models import BaseUserManager
from django.db.models import Manager
from django.utils import timezone


class RoomVisitManager(Manager):
    def visits_for_user(self, user):
        visits = self.filter(user=user).extra(
            select={
                'new_messages': 'SELECT COUNT(*) FROM "phorum_publicmessage" '
                                'WHERE "phorum_publicmessage"."created" > "phorum_roomvisit"."visit_time" '
                                'AND "phorum_publicmessage"."room_id" = "phorum_roomvisit"."room_id"'
            }
        ) \
            .values_list("room", "new_messages")
        return dict(visits)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True,
                                 **extra_fields)
