# -*- coding: utf-8 -*-
"""
Email authentication
"""

from django import VERSION

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class EmailAuthAppConfig(AppConfig):
        name = 'coop_cms.apps.email_auth'
        verbose_name = "coop CMS > Email authentication"
