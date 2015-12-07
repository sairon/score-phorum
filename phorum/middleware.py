class UserActivityMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session')
        if request.user.is_authenticated():
            if "last_action" in request.session:
                del request.session['last_action']
            request.session.modified = True
