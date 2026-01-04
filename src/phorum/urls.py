from django.conf import settings
from django.contrib.auth.views import (
    PasswordResetView as DefaultPasswordResetView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
)
from django.urls import path, re_path

from . import views as phorum_views


class PasswordResetView(DefaultPasswordResetView):
    from_email = settings.SERVER_EMAIL


urlpatterns = [
    path('', phorum_views.room_list, name="home"),
    path('inbox', phorum_views.inbox, name="inbox"),
    path('inbox/new-message', phorum_views.inbox_send, name="inbox_send"),
    path('room/new', phorum_views.room_new, name="room_new"),
    path('room/<room_slug>/', phorum_views.room_view, name="room_view"),
    path('room/<room_slug>/thread/<int:thread_id>/', phorum_views.thread_view, name="thread_view"),
    path('room/<room_slug>/password', phorum_views.room_password_prompt, name="room_password_prompt"),
    path('room/<room_slug>/mark-unread', phorum_views.room_mark_unread, name="room_mark_unread"),
    path('room/<room_slug>/edit', phorum_views.room_edit, name="room_edit"),
    path('room/<room_slug>/new-message', phorum_views.message_send, name="message_send"),
    path('login', phorum_views.login, name="login"),
    path('logout', phorum_views.logout, name="logout"),
    path('user/new', phorum_views.user_new, name="user_new"),
    path('user/edit', phorum_views.user_edit, name="user_edit"),
    path('user/customization', phorum_views.user_customization, name="user_customization"),
    path('users/', phorum_views.users, name="users"),
    path('message/<message_id>/delete', phorum_views.message_delete, name="message_delete"),
    re_path(r'^user/(?P<user_id>\d+)/custom\.(?P<res_type>css|js)$', phorum_views.custom_resource, name="custom_resource"),

    # Password reset links
    path('user/password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('user/password/reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('user/password/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('user/password/reset/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
