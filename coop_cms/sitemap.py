# -*- coding:utf-8 -*-
from django.conf.urls.defaults import url
from django.contrib.sitemaps import Sitemap
from coop_cms.settings import get_article_class
from coop_cms.models import BaseArticle
    
class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        Article = get_article_class()
        return Article.objects.filter(publication=BaseArticle.PUBLISHED)

    def lastmod(self, obj):
        return obj.modified

sitemaps = {
    'coop_cms': ArticleSitemap,
}
urlpatterns = (
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)