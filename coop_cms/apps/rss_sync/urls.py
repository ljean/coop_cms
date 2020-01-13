# -*- coding:utf-8 -*-
"""
urls
"""

from django.conf.urls import url

from coop_cms.apps.rss_sync import views

urlpatterns = [
    url(r'^collect-rss-items/(?P<source_id>\d+)$', views.collect_rss_items_view, name='rss_sync_collect_rss_items'),
    url(r'^create-cms-article/(?P<item_id>\d+)$', views.create_cms_article_view, name='rss_sync_create_cms_article'),
]
