from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('phorum', '0006_publicmessage_deleted_by'),
    ]

    operations = [
        UnaccentExtension(),
    ]
