# -*- coding: utf-8 -*-
"""
Demo
"""

from django import VERSION

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class DemoCmsAppConfig(AppConfig):
        name = 'coop_cms.apps.demo_cms'
        verbose_name = "coop CMS > Demo CMS"
