# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from bs4 import BeautifulSoup
from django.core.urlresolvers import reverse

from model_mommy import mommy

from coop_cms.models import BaseArticle
from coop_cms.settings import is_localized, get_article_class
from coop_cms.tests import BaseArticleTest


class ArticleAdminTest(BaseArticleTest):
    
    def setUp(self):
        self.COOP_CMS_CAN_EDIT_ARTICLE_SLUG = getattr(settings, 'COOP_CMS_CAN_EDIT_ARTICLE_SLUG', None)
        
    def tearDown(self):
        setattr(settings, 'COOP_CMS_CAN_EDIT_ARTICLE_SLUG', self.COOP_CMS_CAN_EDIT_ARTICLE_SLUG)
    
    def test_slug_edition_draft(self):
        settings.COOP_CMS_CAN_EDIT_ARTICLE_SLUG = False
        
        self._log_as_staff_editor()
        
        Article = get_article_class()
        
        article = mommy.make(Article, publication=BaseArticle.DRAFT)
        
        view_name = 'admin:%s_%s_change' % (Article._meta.app_label,  Article._meta.module_name)
        url = reverse(view_name, args=[article.id])
        
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        if is_localized():
            for (lang, _name) in settings.LANGUAGES:
                self.assertEqual(soup.select("#id_"+'slug_'+lang)[0]["type"], "text")
        else:
            self.assertEqual(soup.select("#id_slug")[0]["type"], "text")
                
    def test_slug_edition_published(self):
        settings.COOP_CMS_CAN_EDIT_ARTICLE_SLUG = False
        
        self._log_as_staff_editor()
        
        Article = get_article_class()
        
        article = mommy.make(Article, publication=BaseArticle.PUBLISHED)
        
        view_name = 'admin:%s_%s_change' % (Article._meta.app_label,  Article._meta.module_name)
        url = reverse(view_name, args=[article.id])
        
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        if is_localized():
            for (lang, _name) in settings.LANGUAGES:
                self.assertEqual(soup.select("#id_"+'slug_'+lang)[0]["type"], "hidden")
        else:
            self.assertEqual(soup.select("#id_slug")[0]["type"], "hidden")
                
    def test_slug_edition_published_can_edit(self):
        settings.COOP_CMS_CAN_EDIT_ARTICLE_SLUG = True
        
        self._log_as_staff_editor()
        
        Article = get_article_class()
        
        article = mommy.make(Article, publication=BaseArticle.PUBLISHED)
        
        view_name = 'admin:%s_%s_change' % (Article._meta.app_label,  Article._meta.module_name)
        url = reverse(view_name, args=[article.id])
        
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        if is_localized():
            for (lang, _name) in settings.LANGUAGES:
                self.assertEqual(soup.select("#id_"+'slug_'+lang)[0]["type"], "text")
        else:
            self.assertEqual(soup.select("#id_slug")[0]["type"], "text")
