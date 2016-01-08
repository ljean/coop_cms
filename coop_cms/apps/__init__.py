# -*- coding: utf-8 -*-
"""
Contains several optional applications for coop_cms
"""

from django import VERSION

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class CoopCmsAppConfig(AppConfig):
        name = 'coop_cms'
        verbose_name = "coop CMS"

