from django.conf.urls import patterns, url
from django.contrib.auth.views import (
    password_reset,
    password_reset_complete,
    password_reset_confirm,
    password_reset_done,
)


urlpatterns = patterns(
    "phorum.views",
    url(r'^$', 'room_list', name="home"),
    url(r'^inbox$', 'inbox', name="inbox"),
    url(r'^inbox/new-message$', 'inbox_send', name="inbox_send"),
    url(r'^room/new$', 'room_new', name="room_new"),
    url(r'^room/(?P<room_slug>.+)/$', 'room_view', name="room_view"),
    url(r'^room/(?P<room_slug>.+)/password$', 'room_password_prompt', name="room_password_prompt"),
    url(r'^room/(?P<room_slug>.+)/mark-unread$', 'room_mark_unread', name="room_mark_unread"),
    url(r'^room/(?P<room_slug>.+)/edit$', 'room_edit', name="room_edit"),
    url(r'^room/(?P<room_slug>.+)/new-message$', 'message_send', name="message_send"),
    url(r'^login$', 'login', name="login"),
    url(r'^logout$', 'logout', name="logout"),
    url(r'^user/new', 'user_new', name="user_new"),
    url(r'^user/edit', 'user_edit', name="user_edit"),
    url(r'^user/customization', 'user_customization', name="user_customization"),
    url(r'^users/', 'users', name="users"),
    url(r'^message/(?P<message_id>\d+)/delete', 'message_delete', name="message_delete"),
    url(r'^user/(?P<user_id>\d+)/custom\.(?P<res_type>css|js$)', 'custom_resource', name="custom_resource"),

    # Password reset links
    url(r'^user/password/reset/$', password_reset, name='password_reset'),
    url(r'^user/password/reset/done/$', password_reset_done, name='password_reset_done'),
    url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm, name='password_reset_confirm'),
    url(r'^user/password/reset/complete/$', password_reset_complete, name='password_reset_complete'),
)