# -*- coding: utf-8 -*-
"""
Utilities for Bootstrap CSS framework
"""

from django import VERSION
from __future__ import unicode_literals

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class CoopBootstrapAppConfig(AppConfig):
        name = 'coop_cms.apps.coop_bootstrap'
        verbose_name = "coop CMS > Support of Bootstrap CSS framework"
