# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_homepage(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    site_class = apps.get_model("sites", "Site")
    for site in site_class.objects.all():
        try:
            homepage_article = site.homepage_article
        except models.ObjectDoesNotExist:
            homepage_article = None

        if homepage_article:
            site_settings_class = apps.get_model("coop_cms", "SiteSettings")
            site_settings = site_settings_class.objects.get_or_create(site=site)[0]
            site_settings.homepage_url = homepage_article.get_absolute_url()
            site_settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('coop_cms', '0003_auto_20160204_1540'),
    ]

    operations = [
        migrations.RunPython(set_homepage),
    ]
