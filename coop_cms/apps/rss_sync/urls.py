# -*- coding:utf-8 -*-
"""
urls
"""

from django.urls import path

from . import views

urlpatterns = [
    path('collect-rss-items/<int:source_id>/', views.collect_rss_items_view, name='rss_sync_collect_rss_items'),
    path('create-cms-article/<int:item_id>/', views.create_cms_article_view, name='rss_sync_create_cms_article'),
]
