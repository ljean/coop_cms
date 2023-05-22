# -*- coding: utf-8 -*-
"""
views
"""

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import RssSource, RssItem
from .utils import collect_rss_items, create_cms_article


def collect_rss_items_view(request, source_id):
    """The view called when clicking on the button in the object admin form"""
    rss_source = get_object_or_404(RssSource, id=source_id)
    collect_rss_items(request.user, rss_source)
    url = reverse('admin:rss_sync_rssitem_changelist') + '?source__id__exact={0}'.format(rss_source.id)
    return HttpResponseRedirect(url)


def collect_rss_items_action(modeladmin, request, queryset):
    """The action called when executed from admin list of rss sources"""
    for source in queryset:
        collect_rss_items(request.user, source)
    url = reverse('admin:rss_sync_rssitem_changelist')
    return HttpResponseRedirect(url)


def create_cms_article_view(request, item_id):
    """The view called when clicking on the button in admin object form"""
    item = get_object_or_404(RssItem, id=item_id)
    art = create_cms_article(request.user, item)
    return HttpResponseRedirect(art.get_edit_url())  # redirect to cms article edit page


def create_cms_article_action(modeladmin, request, queryset):
    """The action called when executed from admin list of rss items"""
    for item in queryset:
        art = create_cms_article(request.user, item)

    # if only 1 item processed (checked)
    if queryset.count() == 1:
        return HttpResponseRedirect(art.get_edit_url())  # redirect to cms article edit page


create_cms_article_action.short_description = _('Create CMS Article')
collect_rss_items_action.short_description = _('Collect RSS items')
