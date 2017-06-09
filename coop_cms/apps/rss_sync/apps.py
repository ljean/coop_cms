# -*- coding: utf-8 -*-
"""
Download articles from RSS feeds
"""

from __future__ import unicode_literals


from django.apps import AppConfig

class RssSyncAppConfig(AppConfig):
    name = 'coop_cms.apps.rss_sync'
    verbose_name = "RSS Synchronization"
