# -*- coding: utf-8 -*-
"""Admin forms"""

from __future__ import unicode_literals

from django import forms
from django.conf import settings

from coop_cms.apps.rss_sync import models, widgets

# These 2 admin forms makes possible to add custom widgets for the id field


class RssSourceAdminForm(forms.ModelForm):
    """Admin form"""
    url = forms.CharField(widget=widgets.AdminCollectRssWidget)

    class Meta:
        model = models.RssSource
        fields = ('url', 'title', 'last_collect')

    class Media:
        css = {
            'all': (settings.STATIC_URL + 'css/rss_sync/admin-cust.css',),
        }


class RssItemAdminForm(forms.ModelForm):
    """Admin form"""
    # id = forms.IntegerField(widget=widgets.AdminCreateArticleWidget, label='Id')

    class Meta:
        model = models.RssItem
        fields = ('id', 'source', 'link', 'title', 'summary', 'author', 'updated', 'processed')
        widgets = {
            'id': widgets.AdminCreateArticleWidget,
        }
