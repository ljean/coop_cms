# -*- coding: utf-8 -*-

from django.contrib.syndication.views import Feed
from coop_cms.settings import get_article_class
from coop_cms.utils import dehtml

class ArticleFeed(Feed):
    title = ""
    link = ""
    description = ""

    def items(self):
        Article = get_article_class()
        return Article.objects.filter(category__in_rss=True).order_by('-publication_date')

    def item_title(self, item):
        return dehtml(item.title)

    def item_description(self, item):
        return item.summary