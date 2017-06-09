# -*- coding: utf-8 -*-
"""
utils
"""

from __future__ import unicode_literals

from datetime import datetime
import feedparser
from time import mktime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from coop_cms.apps.rss_sync.models import RssSource, RssItem
from coop_cms.models import BaseArticle
from coop_cms.settings import get_article_class


def collect_rss_items(user, source, check_user_rights=True):
    """
    download a rss feed and create rss_items
    the source can be a RssSource or any object with a get_absolute_url method
    """
    if check_user_rights and (not (user.is_staff and user.has_perm('rss_sync.add_rssitem'))):
        raise PermissionDenied

    feed = feedparser.parse(source.get_absolute_url())
    for entry in feed.entries:
        # create RSS entries if not exists
        item = RssItem.objects.get_or_create(link=entry.link, source=source)[0]
        # In any case, update the data
        item.title = entry.title
        try:
            item.updated = datetime.fromtimestamp(mktime(entry.updated_parsed))
        except AttributeError:
            item.updated = datetime.now()

        item.author = getattr(entry, 'author', '')[:100]
        item.summary = entry.summary
        item.save()

    if isinstance(source, RssSource):
        # update info for rss sources only
        source.title = getattr(feed.feed, 'title', '')
        source.last_collect = datetime.now()
        source.save()


def collect_all_rss_items():
    """collect all items"""
    all_models = getattr(settings, 'RSS_SYNC_SOURCE_MODELS', [RssSource])
    for model in all_models:
        for source in model.objects.all():
            collect_rss_items(None, source, check_user_rights=False)


def create_cms_article(user, item):
    """create a cms coop_cms.article from a RssItem"""
    article_class = get_article_class()
    content_type = ContentType.objects.get_for_model(article_class)
    perm = '{0}.add_{1}'.format(content_type.app_label, content_type.model)

    if not (user.is_staff and user.has_perm(perm)):
        raise PermissionDenied

    art = article_class.objects.create(title=item.title, content=item.summary, publication=BaseArticle.DRAFT)
    item.processed = True
    item.save()
    return art
