# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import phorum.models
import phorum.models.fields
import phorum.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('phorum', '0002_auto_20160330_2012'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCustomization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('custom_css', phorum.models.fields.RawContentFileField(storage=phorum.models.OverwritingFileSystemStorage(base_url=b'/protected', location=b'/home/kpt/projects/score-phorum/protected'), upload_to=phorum.models.utils.css_upload_path, null=True, verbose_name=b'Vlastn\xc3\xad CSS', blank=True)),
                ('custom_js', phorum.models.fields.RawContentFileField(storage=phorum.models.OverwritingFileSystemStorage(base_url=b'/protected', location=b'/home/kpt/projects/score-phorum/protected'), upload_to=phorum.models.utils.js_upload_path, null=True, verbose_name=b'Vlastn\xc3\xad JS', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
