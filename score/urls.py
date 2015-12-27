"""score URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'phorum.views.room_list', name="home"),
    url(r'^inbox$', 'phorum.views.inbox', name="inbox"),
    url(r'^inbox/new-message$', 'phorum.views.inbox_send', name="inbox_send"),
    url(r'^room/new$', 'phorum.views.room_new', name="room_new"),
    url(r'^room/(?P<room_slug>.+)/$', 'phorum.views.room_view', name="room_view"),
    url(r'^room/(?P<room_slug>.+)/password$', 'phorum.views.room_password_prompt', name="room_password_prompt"),
    url(r'^room/(?P<room_slug>.+)/mark-unread$', 'phorum.views.room_mark_unread', name="room_mark_unread"),
    url(r'^room/(?P<room_slug>.+)/edit$', 'phorum.views.room_edit', name="room_edit"),
    url(r'^room/(?P<room_slug>.+)/new-message$', 'phorum.views.message_send', name="message_send"),
    url(r'^login$', 'phorum.views.login', name="login"),
    url(r'^logout$', 'phorum.views.logout', name="logout"),
    url(r'^user/new', 'phorum.views.user_new', name="user_new"),
    url(r'^user/edit', 'phorum.views.user_edit', name="user_edit"),
    url(r'^users/', 'phorum.views.users', name="users"),
    url(r'^message/(?P<message_id>\d+)/delete', 'phorum.views.message_delete', name="message_delete"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
