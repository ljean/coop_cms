# -*- coding: utf-8 -*-
"""
Download articles from RSS feeds
"""

from django import VERSION
from __future__ import unicode_literals

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class RssSyncAppConfig(AppConfig):
        name = 'coop_cms.apps.rss_sync'
        verbose_name = "RSS Synchronization"
