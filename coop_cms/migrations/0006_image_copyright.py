# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop_cms', '0005_articlecategory_pagination_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='copyright',
            field=models.CharField(default=b'', max_length=200, verbose_name='copyright', blank=True),
        ),
    ]
