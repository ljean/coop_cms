# -*- coding: utf-8 -*-
"""
Unit tests
"""

from __future__ import unicode_literals

from unittest import skipUnless

from django.contrib.auth.models import User
from django.conf import settings
from django.test import TestCase

from model_mommy import mommy

from coop_cms.settings import get_article_class


@skipUnless('coop_cms.apps.demo_cms' in settings.INSTALLED_APPS, "demo_cms not installed installed")
class AuthorPermissionTest(TestCase):
    """test author permission is taken into account"""

    def setUp(self):
        """called before every test"""
        if hasattr(get_article_class, '_cache_class'):
            delattr(get_article_class, '_cache_class')
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.PrivateArticle'
        self.user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')

    def tearDown(self):
        """called after every test"""
        delattr(get_article_class, '_cache_class')
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'

    def test_view_private_article(self):
        """test user can view his private article"""
        article = mommy.make(get_article_class(), author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)

    def test_cant_view_private_article(self):
        """test user can not view other user private article"""
        article = mommy.make(get_article_class())

        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)

        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)

    def test_edit_private_article(self):
        """test user can edit own private article"""
        article = mommy.make(get_article_class(), author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        data = {'title': 'A', 'content': 'B', 'author': article.author.id}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(200, response.status_code)
        article = get_article_class().objects.get(id=article.id)#refresh
        self.assertEqual('A', article.title)
        self.assertEqual('B', article.content)

    def test_cant_edit_private_article(self):
        """test user can not edit other user article"""
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.DRAFT)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        data = {'title': 'A', 'content': 'B', 'author': None}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        article = get_article_class().objects.get(id=article.id)#refresh
        self.assertNotEqual('A', article.title)
        self.assertNotEqual('B', article.content)

    def test_publish_private_article(self):
        """test user can publish own private article"""
        klass = get_article_class()
        article = mommy.make(klass, author=self.user, publication=klass.DRAFT)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_publish_url(), data={'publication':klass.PUBLISHED}, follow=True)
        self.assertEqual(200, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.publication, klass.PUBLISHED)

    def test_cant_publish_private_article(self):
        """test user can not publish others private article"""
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.DRAFT)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_publish_url(), data={'publication':klass.PUBLISHED}, follow=True)
        self.assertEqual(403, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.publication, klass.DRAFT)

    def test_can_change_author_article(self):
        """test user can change author"""
        klass = get_article_class()
        article = mommy.make(klass, author=self.user, publication=klass.PUBLISHED)

        titi = User.objects.create_user('titi', 'titi@toto.fr', 'toto')

        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        data = {'title': 'A', 'content': 'B', 'author': titi.id}
        response = self.client.post(article.get_edit_url(), data=data, follow=False)
        self.assertEqual(302, response.status_code)

        article = klass.objects.get(id=article.id)  # refresh
        self.assertEqual(article.author, titi)
