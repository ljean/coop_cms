# -*- coding: utf-8 -*-

from django.test import TestCase
from django.conf import settings
from model_mommy import mommy
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from coop_cms.settings import get_article_class
from unittest import skipUnless

@skipUnless('coop_cms.apps.demo_cms' in settings.INSTALLED_APPS, "demo_cms not installed installed")
class AuthorPermissionTest(TestCase):

    def setUp(self):
        if hasattr(get_article_class, '_cache_class'):
            delattr(get_article_class, '_cache_class')
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.PrivateArticle'
        self.user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
    def tearDown(self):
        delattr(get_article_class, '_cache_class')
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'
    
    def test_view_private_article(self):
        article = mommy.make(get_article_class(), author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_cant_view_private_article(self):
        article = mommy.make(get_article_class())
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
    def test_edit_private_article(self):
        article = mommy.make(get_article_class(), author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_edit_url(), data={'title': 'A', 'content': 'B', 'author': article.author.id}, follow=True)
        #self.assertEqual(200, self.client.get(article.get_absolute_url()).status_code)
        self.assertEqual(200, response.status_code)
        article = get_article_class().objects.get(id=article.id)#refresh
        self.assertEqual('A', article.title)
        self.assertEqual('B', article.content)
        
    def test_cant_edit_private_article(self):
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.DRAFT)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_edit_url(), data={'title': 'A', 'content': 'B', 'author': None}, follow=True)
        self.assertEqual(403, response.status_code)
        article = get_article_class().objects.get(id=article.id)#refresh
        self.assertNotEqual('A', article.title)
        self.assertNotEqual('B', article.content)
        
    def test_publish_private_article(self):
        klass = get_article_class()
        article = mommy.make(klass, author=self.user, publication=klass.DRAFT)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_publish_url(), data={'publication':klass.PUBLISHED}, follow=True)
        self.assertEqual(200, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.publication, klass.PUBLISHED)
        
    def test_cant_publish_private_article(self):
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.DRAFT)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_publish_url(), data={'publication':klass.PUBLISHED}, follow=True)
        self.assertEqual(403, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.publication, klass.DRAFT)
        
    def test_can_change_author_article(self):
        klass = get_article_class()
        article = mommy.make(klass, author=self.user, publication=klass.PUBLISHED)
        
        titi = User.objects.create_user('titi', 'titi@toto.fr', 'toto')
        
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_edit_url(), data={'title': 'A', 'content': 'B', 'author': titi.id}, follow=False)
        self.assertEqual(302, response.status_code)
        
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.author, titi)
        