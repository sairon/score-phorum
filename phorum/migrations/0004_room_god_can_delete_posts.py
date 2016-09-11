# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phorum', '0003_usercustomization'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='god_can_delete_posts',
            field=models.BooleanField(default=True),
        ),
    ]
