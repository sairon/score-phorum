import django.contrib.sessions.middleware
from django.utils.deprecation import MiddlewareMixin
import user_sessions.middleware


class UserSessionsMiddleware(
  user_sessions.middleware.SessionMiddleware,
  django.contrib.sessions.middleware.SessionMiddleware,
):
    pass


class UserActivityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session')
        if request.user.is_authenticated:
            if "last_action" in request.session:
                del request.session['last_action']
            request.session.modified = True
