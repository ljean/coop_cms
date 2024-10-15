# -*- coding: utf-8 -*-
"""
Email authentication
"""

from django.apps import AppConfig


class EmailAuthAppConfig(AppConfig):
    name = 'coop_cms.apps.email_auth'
    verbose_name = "coop CMS > Email authentication"
    default_auto_field = 'django.db.models.BigAutoField'
