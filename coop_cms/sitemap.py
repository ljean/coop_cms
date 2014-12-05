# -*- coding:utf-8 -*-
"""sitemaps"""

from django.db.models import Q
from django.conf import settings
from django.conf.urls import url
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from coop_cms.models import BaseArticle, SiteSettings
from coop_cms.settings import get_article_class, is_localized

if is_localized():
    from localeurl.sitemaps import LocaleurlSitemap # pylint: disable=F0401
    base_sitemap_class = LocaleurlSitemap
else:
    base_sitemap_class = Sitemap


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


class BaseSitemap(base_sitemap_class):
    _current_site = None

    def __init__(self, language, site):
        if is_localized():
            super(BaseSitemap, self).__init__(language)
        else:
            super(BaseSitemap, self).__init__()
        self._site = site

    def get_urls(self, page=1, site=None, protocol=None):
        return super(BaseSitemap, self).get_urls(page, self._site, protocol=protocol)

    def get_current_site(self):
        if not self._current_site:
            self._current_site = Site.objects.get_current()
        return self._current_site


class ArticleSitemap(BaseSitemap):
    """article sitemap"""
    changefreq = "weekly"
    priority = 0.5
    _sitemap_mode = None

    def get_sitemap_mode(self):
        site = self.get_current_site()
        if not self._sitemap_mode:
            try:
                self._sitemap_mode = site.sitesettings.sitemap_mode
            except SiteSettings.DoesNotExist:
                self._sitemap_mode = SiteSettings.SITEMAP_ONLY_SITE
        return self._sitemap_mode

    def items(self):
        """items"""
        article_class = get_article_class()

        sitemap_mode = self.get_sitemap_mode()

        queryset = article_class.objects.filter(publication=BaseArticle.PUBLISHED)

        if self._site == self.get_current_site():
            return queryset.filter(sites=self._site)
        else:
            if sitemap_mode == SiteSettings.SITEMAP_ONLY_SITE:
                #Only the articles of current sites
                return article_class.objects.none()
            elif sitemap_mode == SiteSettings.SITEMAP_ALL:
                #Articles of which are only on the site and not in current site
                return queryset.filter(sites=self._site).exclude(sites=self.get_current_site())

    def lastmod(self, obj):
        """item last modification"""
        return obj.modified


def get_sitemaps(langs=None):
    """return sitemaps"""
    sitemaps = {}
    sites = Site.objects.all()
    if is_localized():
        lang_codes = langs or [code for (code, _x) in settings.LANGUAGES]
        for code in lang_codes:
            for site in sites:
                site_suffix = "_{0}_{1}".format(site.id, code)
                sitemaps['coop_cms{0}'.format(site_suffix)] = ArticleSitemap(code, site)
    else:
        for site in sites:
            site_suffix = "_{0}".format(site.id)
            sitemaps['coop_cms{0}'.format(site_suffix)] = ArticleSitemap(None, site)
    return sitemaps


urlpatterns = (
    url(
        r'^sitemap\.xml$',
        'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': get_sitemaps},
        name="coop_cms_sitemap"
    ),
)
