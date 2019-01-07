# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import autoslug.fields
import phorum.models.managers
from django.conf import settings
import django.utils.timezone
import phorum.models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(unique=True, max_length=32, error_messages={b'unique': 'A user with that username already exists.'})),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('kredyti', models.PositiveIntegerField(default=0)),
                ('level_override', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(0, b'Green ribbon'), (1, b'Yellow ribbon'), (2, b'Orange ribbon'), (3, b'Red ribbon'), (4, b'Crimson ribbon'), (5, b'1 dot'), (6, b'2 dots'), (7, b'3 dots'), (8, b'God'), (15, b'Admin'), (16, b'Editor'), (99, b'Dev')])),
                ('motto', models.CharField(max_length=64, blank=True)),
                ('avatar', models.ImageField(upload_to=b'avatars', blank=True)),
                ('inbox_visit_time', models.DateTimeField(null=True, blank=True)),
                ('last_ip', models.GenericIPAddressField(null=True, blank=True)),
                ('max_thread_roots', models.SmallIntegerField(default=10, verbose_name=b'po\xc4\x8det thread\xc5\xaf na str\xc3\xa1nku', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(50)])),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', phorum.models.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', phorum.models.MessageTextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_reply', phorum.models.LastReplyField(null=True, blank=True)),
                ('author', models.ForeignKey(related_name='posted_privatemessage', to=settings.AUTH_USER_MODEL)),
                ('recipient', models.ForeignKey(related_name='received_privatemessage', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('thread', models.ForeignKey(related_name='children', blank=True, to='phorum.PrivateMessage', null=True)),
            ],
            options={
                'ordering': ['created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PublicMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', phorum.models.MessageTextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_reply', phorum.models.LastReplyField(null=True, blank=True)),
                ('author', models.ForeignKey(related_name='posted_publicmessage', to=settings.AUTH_USER_MODEL)),
                ('recipient', models.ForeignKey(related_name='received_publicmessage', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, populate_from=b'name', editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('password', models.CharField(max_length=128, blank=True)),
                ('password_changed', models.DateTimeField(null=True, blank=True)),
                ('pinned', models.BooleanField(default=False)),
                ('author', models.ForeignKey(related_name='created_rooms', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('moderator', models.ForeignKey(related_name='moderated_rooms', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-pinned', 'name'),
            },
        ),
        migrations.CreateModel(
            name='RoomVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visit_time', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(to='phorum.Room')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserRoomKeyring',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_successful_entry', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(to='phorum.Room')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='room',
            name='visits',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='phorum.RoomVisit'),
        ),
        migrations.AddField(
            model_name='publicmessage',
            name='room',
            field=models.ForeignKey(to='phorum.Room'),
        ),
        migrations.AddField(
            model_name='publicmessage',
            name='thread',
            field=models.ForeignKey(related_name='children', blank=True, to='phorum.PublicMessage', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='room_keyring',
            field=models.ManyToManyField(to='phorum.Room', through='phorum.UserRoomKeyring'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
    ]
