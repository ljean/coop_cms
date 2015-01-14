# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from django.contrib.sites.models import Site
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory

from model_mommy import mommy

from coop_cms.models import BaseArticle, SiteSettings
from coop_cms.settings import get_article_class
from coop_cms.sitemap import get_sitemaps


class SitemapTest(TestCase):
    
    def setUp(self):
        self._site2 = mommy.make(Site, id=settings.SITE_ID+1)

    def test_sitemap_empty(self):
        url = reverse("coop_cms_sitemap")
        factory = RequestFactory()
        request = factory.get(url)
        response = sitemap_view(request, get_sitemaps())
        self.assertEqual(200, response.status_code)
    
    def test_sitemap(self):
        site = Site.objects.get_current()
        site2 = self._site2
        
        article_class = get_article_class()
        
        article1 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article2 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article3 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article4 = mommy.make(article_class, publication=BaseArticle.DRAFT)
        
        article2.sites.add(site2)
        article2.save()
        
        article3.sites.remove(site)
        article3.sites.add(site2)
        article3.save()

        factory = RequestFactory()
        request = factory.get('/sitemap.xml')
        response = sitemap_view(request, get_sitemaps())

        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, site.domain+article1.get_absolute_url())
        self.assertContains(response, site.domain+article2.get_absolute_url())
        self.assertNotContains(response, article3.get_absolute_url())
        self.assertNotContains(response, article4.get_absolute_url())

    def test_sitemap_only_site(self):
        site = Site.objects.get_current()
        site2 = self._site2

        site_settings = mommy.make(SiteSettings, site=site, sitemap_mode=SiteSettings.SITEMAP_ONLY_SITE)

        article_class = get_article_class()

        article1 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article2 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article3 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article4 = mommy.make(article_class, publication=BaseArticle.DRAFT)

        article2.sites.add(site2)
        article2.save()

        article3.sites.remove(site)
        article3.sites.add(site2)
        article3.save()

        factory = RequestFactory()
        request = factory.get('/sitemap.xml')
        response = sitemap_view(request, get_sitemaps())

        self.assertEqual(200, response.status_code)

        self.assertContains(response, site.domain+article1.get_absolute_url())
        self.assertContains(response, site.domain+article2.get_absolute_url())
        self.assertNotContains(response, article3.get_absolute_url())
        self.assertNotContains(response, article4.get_absolute_url())

    def test_sitemap_all(self):
        site = Site.objects.get_current()
        site2 = self._site2

        site_settings = mommy.make(SiteSettings, site=site, sitemap_mode=SiteSettings.SITEMAP_ALL)

        article_class = get_article_class()

        article1 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article2 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article3 = mommy.make(article_class, publication=BaseArticle.PUBLISHED)
        article4 = mommy.make(article_class, publication=BaseArticle.DRAFT)

        article2.sites.add(site2)
        article2.save()

        article3.sites.remove(site)
        article3.sites.add(site2)
        article3.save()

        factory = RequestFactory()
        request = factory.get('/sitemap.xml')
        response = sitemap_view(request, get_sitemaps())

        self.assertEqual(200, response.status_code)

        self.assertContains(response, site.domain+article1.get_absolute_url())
        self.assertContains(response, site.domain+article2.get_absolute_url())
        self.assertContains(response, site2.domain+article3.get_absolute_url())
        self.assertNotContains(response, article4.get_absolute_url())
