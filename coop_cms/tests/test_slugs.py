# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from unittest import skipIf

from django.contrib.sites.models import Site
from django.utils.translation import activate, get_language

from coop_cms.settings import is_localized, is_multilang, get_article_class
from coop_cms.tests import BaseTestCase


class ArticleSlugTestCase(BaseTestCase):
    
    def tearDown(self):
        super(ArticleSlugTestCase, self).tearDown()
        site1 = Site.objects.all()[0]
        settings.SITE_ID = site1.id
    
    def test_create_article_same_title(self):
        Article = get_article_class()
        article1 = Article.objects.create(title="Titre de l'article")
        for x in xrange(12):
            article2 = Article.objects.create(title=article1.title)
            self.assertNotEqual(article1.slug, article2.slug)
            self.assertEqual(article1.title, article2.title)
        response = self.client.get(article2.get_absolute_url())
        self.assertEqual(200, response.status_code)
        response = self.client.get(article1.get_absolute_url())
        self.assertEqual(200, response.status_code)
            
    def test_create_article_same_different_sites(self):
        Article = get_article_class()
        article1 = Article.objects.create(title="Titre de l'article")
        
        site1 = Site.objects.all()[0]
        site2 = Site.objects.create(domain='hhtp://test2', name="Test2")
        settings.SITE_ID = site2.id
        
        article2 = Article.objects.create(title=article1.title)
        self.assertNotEqual(article1.slug, article2.slug)
        self.assertEqual(article1.title, article2.title)
        
        response = self.client.get(article1.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
        response = self.client.get(article2.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
        settings.SITE_ID = site1.id
        response = self.client.get(article1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_create_lang(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title="Titre de l'article")
        a2 = Article.objects.create(title=a1.title)
        self.assertNotEqual(a1.slug, a2.slug)
        self.assertEqual(a1.title, a2.title)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
            
        setattr(a1, 'title_'+trans_lang, 'This is the title')
        a1.save()
        
        setattr(a2, 'title_'+trans_lang, getattr(a1, 'title_'+trans_lang))
        a2.save()
        
        a1 = Article.objects.get(id=a1.id)
        a2 = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a1, 'title_'+trans_lang), getattr(a2, 'title_'+trans_lang))
        self.assertNotEqual(getattr(a1, 'slug_'+trans_lang), getattr(a2, 'slug_'+trans_lang))
        
    def _get_localized_slug(self, slug):
        if is_localized():
            from localeurl.utils import locale_path
            locale = get_language()                
            return locale_path(slug, locale)
        return slug
    
    def test_create_article_html_in_title(self):
        Article = get_article_class()
        article1 = Article.objects.create(title="<h1>Titre de l'article</h1>")
        response = self.client.get(article1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
        expected_title = self._get_localized_slug("/titre-de-larticle/")
        self.assertEqual(article1.get_absolute_url(), expected_title)
        
    def test_create_article_complex_html_in_title(self):
        Article = get_article_class()
        article1 = Article.objects.create(title="<p><h2>Titre de <b>l'article</b><h2><div></div></p>")
        response = self.client.get(article1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        expected_title = self._get_localized_slug("/titre-de-larticle/")
        self.assertEqual(article1.get_absolute_url(), expected_title)
