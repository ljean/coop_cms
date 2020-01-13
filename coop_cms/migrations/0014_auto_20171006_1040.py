# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop_cms', '0013_auto_20170607_1508'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='fragment',
            unique_together=set([('type', 'name', 'filter')]),
        ),
    ]
