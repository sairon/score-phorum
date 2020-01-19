from functools import partial

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.views import (
    PasswordResetView as DefaultPasswordResetView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
)

from . import views as phorum_views


class PasswordResetView(DefaultPasswordResetView):
    from_email = settings.SERVER_EMAIL


urlpatterns = [
    url(r'^$', phorum_views.room_list, name="home"),
    url(r'^inbox$', phorum_views.inbox, name="inbox"),
    url(r'^inbox/new-message$', phorum_views.inbox_send, name="inbox_send"),
    url(r'^room/new$', phorum_views.room_new, name="room_new"),
    url(r'^room/(?P<room_slug>.+)/$', phorum_views.room_view, name="room_view"),
    url(r'^room/(?P<room_slug>.+)/password$', phorum_views.room_password_prompt, name="room_password_prompt"),
    url(r'^room/(?P<room_slug>.+)/mark-unread$', phorum_views.room_mark_unread, name="room_mark_unread"),
    url(r'^room/(?P<room_slug>.+)/edit$', phorum_views.room_edit, name="room_edit"),
    url(r'^room/(?P<room_slug>.+)/new-message$', phorum_views.message_send, name="message_send"),
    url(r'^login$', phorum_views.login, name="login"),
    url(r'^logout$', phorum_views.logout, name="logout"),
    url(r'^user/new', phorum_views.user_new, name="user_new"),
    url(r'^user/edit', phorum_views.user_edit, name="user_edit"),
    url(r'^user/customization', phorum_views.user_customization, name="user_customization"),
    url(r'^users/', phorum_views.users, name="users"),
    url(r'^message/(?P<message_id>\d+)/delete', phorum_views.message_delete, name="message_delete"),
    url(r'^user/(?P<user_id>\d+)/custom\.(?P<res_type>css|js$)', phorum_views.custom_resource, name="custom_resource"),

    # Password reset links
    url(r'^user/password/reset/$', PasswordResetView.as_view(), name='password_reset'),
    url(r'^user/password/reset/done/$', PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^user/password/reset/complete/$', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
