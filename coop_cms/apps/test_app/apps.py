# -*- coding: utf-8 -*-
"""
Applicaion for unit testing
"""

from django import VERSION

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class CoopCmsTestAppConfig(AppConfig):
        name = 'coop_cms.apps.test_app'
        verbose_name = "coop CMS > App for unit test"
