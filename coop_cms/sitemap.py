# -*- coding:utf-8 -*-
"""sitemaps"""

from django.conf import settings
from django.conf.urls import url
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from coop_cms.models import BaseArticle
from coop_cms.settings import get_article_class


class ViewSitemap(Sitemap):
    """Sitemap base class for django view"""
    view_names = []
    
    def items(self):
        """get items"""
        class Klass(object):
            def __init__(self, name):
                self.name = name
            
            def get_absolute_url(self):
                return reverse(self.name)
            
        return [Klass(x) for x in self.view_names]


class ArticleSitemap(Sitemap):
    """article sitemap"""
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        """items"""
        article_class = get_article_class()
        return article_class.objects.filter(
            publication=BaseArticle.PUBLISHED, sites=Site.objects.get_current()
        )

    def lastmod(self, obj):
        """item last modification"""
        return obj.modified


def get_sitemaps(langs=None):
    """return sitemaps"""
    if 'localeurl' in settings.INSTALLED_APPS:
        from localeurl.sitemaps import LocaleurlSitemap # pylint: disable=F0401
        class LocaleArticleSitemap(LocaleurlSitemap, ArticleSitemap): pass
        sitemaps = {}
        lang_codes = langs or [code for (code, _x) in settings.LANGUAGES]
        for code in lang_codes:
            sitemaps['coop_cms_'+code] = LocaleArticleSitemap(code) 
    else:
        sitemaps = {
            'coop_cms': ArticleSitemap,
        }
    return sitemaps


urlpatterns = (
    url(
        r'^sitemap\.xml$',
        'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': get_sitemaps()},
        name="coop_cms_sitemap"
    ),
)