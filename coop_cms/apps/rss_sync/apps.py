# -*- coding: utf-8 -*-
"""
Download articles from RSS feeds
"""

from django import VERSION

if VERSION > (1, 7, 0):
    from django.apps import AppConfig

    class RssSyncAppConfig(AppConfig):
        name = 'coop_cms.apps.rss_sync'
        verbose_name = "RSS Synchronization"
