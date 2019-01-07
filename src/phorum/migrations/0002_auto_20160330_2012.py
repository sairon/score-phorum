# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phorum', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['username'], 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
        migrations.AlterField(
            model_name='user',
            name='level_override',
            field=models.PositiveSmallIntegerField(blank=True, null=True, choices=[(0, b'Green ribbon'), (1, b'Yellow ribbon'), (2, b'Orange ribbon'), (3, b'Red ribbon'), (4, b'Maroon ribbon'), (5, b'1 dot'), (6, b'2 dots'), (7, b'3 dots'), (8, b'God'), (15, b'Admin'), (16, b'Editor'), (99, b'Dev')]),
        ),
    ]
