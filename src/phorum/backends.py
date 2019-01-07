from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
            else:
                return None
        except user_model.DoesNotExist:
            return None
