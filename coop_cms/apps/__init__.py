# -*- coding: utf-8 -*-
"""
Contains several optional applications for coop_cms
"""

from django.apps import AppConfig


class CoopCmsAppConfig(AppConfig):
    name = 'coop_cms'
    verbose_name = "coop CMS"
    default_auto_field = 'django.db.models.BigAutoField'
