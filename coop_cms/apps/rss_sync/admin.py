# -*- coding: utf-8 -*-
"""
Admin
"""

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from coop_cms.apps.rss_sync import models, views
from coop_cms.apps.rss_sync.forms import RssSourceAdminForm, RssItemAdminForm


@admin.register(models.RssSource)
class RssSourceAdmin(admin.ModelAdmin):
    """Rss source admin"""

    list_display = ('url', 'title', 'last_collect')
    readonly_fields = ('title', 'last_collect')
    fieldsets = (
        (_('Feed'), {'fields': ('url',)}),
        (_('Information'), {'fields': ('title', 'last_collect')}),
    )
    actions = [views.collect_rss_items_action]

    def get_form(self, request, obj=None, **kwargs):
        """returns custom form"""
        defaults = dict(kwargs)
        if obj:
            defaults.update({
                'form': RssSourceAdminForm,
            })
        return super(RssSourceAdmin, self).get_form(request, obj, **defaults) # pylint: disable=E1002


@admin.register(models.RssItem)
class RssItemAdmin(admin.ModelAdmin):
    """Rss Item admin"""
    form = RssItemAdminForm
    list_display = ('link', 'source', 'title', 'updated', 'processed')
    list_filter = ('source', 'processed')
    readonly_fields = ('source', 'link', 'updated', 'processed')
    fieldsets = (
        (_('Actions'), {'fields': ('id',)}),
        (_('Source'), {'fields': ('source', 'link', 'updated')}),
        (_('Content'), {'fields': ('title', 'summary')}),
        (_('CMS'), {'fields': ('processed',)}),
    )
    actions = [views.create_cms_article_action]
