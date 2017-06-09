# -*- coding: utf-8 -*-
"""
Email authentication
"""

from django import VERSION
from __future__ import unicode_literals

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class EmailAuthAppConfig(AppConfig):
        name = 'coop_cms.apps.email_auth'
        verbose_name = "coop CMS > Email authentication"
