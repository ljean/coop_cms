# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

import json
from unittest import skipIf

from django.contrib.auth.models import User, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.test import TestCase
from django.test.client import RequestFactory

from coop_cms.models import Link, NavNode, BaseArticle
from coop_cms.settings import is_localized, is_multilang, get_article_class, get_navtree_class
from coop_cms.templatetags.coop_utils import get_part, get_parts
from coop_cms.tests import BaseTestCase


class CmsEditTagTest(BaseTestCase):

    def setUp(self):
        super(CmsEditTagTest, self).setUp()

        self.link1 = Link.objects.create(url='http://www.google.fr')
        self.tree = tree = get_navtree_class().objects.create()
        NavNode.objects.create(tree=tree, label=self.link1.url, content_object=self.link1, ordering=1, parent=None)

    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')

        ct = ContentType.objects.get_for_model(get_article_class())

        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)

        perm = 'add_{0}'.format(ct.model)
        can_add_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add_article)

        user.is_active = True
        user.save()

        return self.client.login(username='toto', password='toto')

    def _create_article(self):
        Article = get_article_class()
        article = Article.objects.create(
            title='test', content='<h1>Ceci est un test</h1>', publication=BaseArticle.PUBLISHED,
            template="test/nav_tag_in_edit_tag.html")
        NavNode.objects.create(tree=self.tree, label=article.title, content_object=article, ordering=1, parent=None)
        return article

    def test_view_navigation_inside_cms_edit_tag_visu(self):
        article = self._create_article()

        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)

        self.assertContains(response, "Hello") #text in template
        self.assertContains(response, article.content)
        self.assertContains(response, self.link1.url)

    def test_view_navigation_inside_cms_edit_tag_edition(self):
        self._log_as_editor()
        article = self._create_article()

        response = self.client.get(article.get_edit_url(), follow=True)
        self.assertEqual(200, response.status_code)

        self.assertContains(response, "Hello")
        self.assertContains(response, article.content)
        self.assertContains(response, self.link1.url)


class ArticleTemplateTagsTest(BaseTestCase):

    def _request(self):
        class DummyRequest:
            def __init__(self):
                self.LANGUAGE_CODE = settings.LANGUAGES[0][0]
        return DummyRequest()

    def test_create_article_link(self):
        tpl = Template('{% load coop_utils %}{% article_link "test" %}')
        html = tpl.render(Context({'request': self._request()}))

        Article = get_article_class()
        self.assertEqual(Article.objects.count(), 1)
        a = Article.objects.all()[0]
        self.assertEqual(a.slug, "test")

    def test_existing_article(self):
        Article = get_article_class()

        article = Article.objects.create(slug="test", title="Test")

        tpl = Template('{% load coop_utils %}{% article_link "test" %}')
        html = tpl.render(Context({'request': self._request()}))

        self.assertEqual(Article.objects.count(), 1)
        a = Article.objects.all()[0]
        self.assertEqual(a.slug, "test")

    @skipIf(len(settings.LANGUAGES)==0, "not languages")
    def test_article_link_language(self):

        lang = settings.LANGUAGES[0][0]

        tpl = Template('{% load coop_utils %}{% article_link "test" '+lang+' %}')
        html = tpl.render(Context({'request': self._request()}))

        Article = get_article_class()
        self.assertEqual(Article.objects.count(), 1)
        a = Article.objects.all()[0]
        self.assertEqual(a.slug, "test")

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_article_link_force_language(self):

        lang = settings.LANGUAGES[0][0]

        tpl = Template('{% load coop_utils %}{% article_link "test" '+lang+' %}')
        request = self._request()
        request.LANGUAGE_CODE = settings.LANGUAGES[1][0]
        html = tpl.render(Context({'request': request}))

        Article = get_article_class()
        self.assertEqual(Article.objects.count(), 1)
        a = Article.objects.all()[0]
        self.assertEqual(a.slug, "test")

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_article_existing_link_force_language(self):

        Article = get_article_class()

        lang = settings.LANGUAGES[0][0]

        article = Article.objects.create(slug="test", title="Test")

        request = self._request()
        lang = request.LANGUAGE_CODE = settings.LANGUAGES[1][0]

        setattr(article, "slug_"+lang, "test_"+lang)
        article.save()

        tpl = Template('{% load coop_utils %}{% article_link "test" '+lang+' %}')
        html = tpl.render(Context({'request': request}))

        self.assertEqual(Article.objects.count(), 1)
        a = Article.objects.all()[0]
        self.assertEqual(a.slug, "test")
        self.assertEqual(getattr(article, "slug_"+lang), "test_"+lang)

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_article_existing_link_force_default_language(self):

        Article = get_article_class()

        article = Article.objects.create(title="Test")

        request = self._request()
        def_lang = settings.LANGUAGES[0][0]
        cur_lang = request.LANGUAGE_CODE = settings.LANGUAGES[1][0]

        #activate(cur_lang)
        setattr(article, "slug_"+cur_lang, "test_"+cur_lang)
        article.save()

        count = Article.objects.count()

        tpl = Template('{% load coop_utils %}{% article_link "test" '+def_lang+' %}')
        html = tpl.render(Context({'request': request}))

        self.assertEqual(Article.objects.count(), count)
        a = Article.objects.get(id=article.id)
        self.assertEqual(a.slug, "test")
        self.assertEqual(getattr(a, "slug_"+cur_lang), "test_"+cur_lang)


class PartitionTemplateFilterTest(TestCase):
    
    def test_get_part_exact(self):
        objs = range(9)
        self.assertEqual([0, 1, 2], get_part(objs, "1/3"))
        self.assertEqual([3, 4, 5], get_part(objs, "2/3"))
        self.assertEqual([6, 7, 8], get_part(objs, "3/3"))
    
    def test_get_part_inexact(self):
        objs = range(10)
        self.assertEqual([0, 1, 2, 3], get_part(objs, "1/3"))
        self.assertEqual([4, 5, 6,], get_part(objs, "2/3"))
        self.assertEqual([7, 8, 9], get_part(objs, "3/3"))
        
    def test_get_part_empty(self):
        objs = []
        self.assertEqual([], get_part(objs, "1/3"))
        self.assertEqual([], get_part(objs, "2/3"))
        self.assertEqual([], get_part(objs, "3/3"))
    
    def test_get_part_less_than(self):
        objs = [0, 1]
        self.assertEqual([0], get_part(objs, "1/3"))
        self.assertEqual([1], get_part(objs, "2/3"))
        self.assertEqual([], get_part(objs, "3/3"))
        
    def test_get_parts_exact(self):
        objs = range(9)
        self.assertEqual([[0, 1, 2], [3, 4, 5], [6, 7, 8]], get_parts(objs, 3))
        
    def test_get_parts_inexact(self):
        objs = range(10)
        self.assertEqual([[0, 1, 2, 3], [4, 5, 6,], [7, 8, 9]], get_parts(objs, 3))

    def test_get_parts_empty(self):
        objs = []
        self.assertEqual([[], [], []], get_parts(objs, 3))
    
    def test_get_parts_less_than(self):
        objs = [0, 1]
        self.assertEqual([[0], [1], []], get_parts(objs, 3))


class AcceptCookieMessageTest(BaseTestCase):

    def test_get_hide_accept_cookies(self):

        url = reverse("coop_cms_hide_accept_cookies_message")
        response = self.client.get(url)

        self.assertEqual(404, response.status_code)

        self.assertEqual(self.client.session.get('hide_accept_cookie_message', None), None)


    def test_post_hide_accept_cookies(self):

        url = reverse("coop_cms_hide_accept_cookies_message")
        response = self.client.post(url)

        self.assertEqual(200, response.status_code)

        json_content = json.loads(response.content)
        self.assertEqual(json_content["Ok"], True)

        self.assertEqual(self.client.session.get('hide_accept_cookie_message'), True)


    def test_view_accept_cookies_message(self, ):
        tpl = Template('{% load coop_utils %}{% show_accept_cookie_message %}')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        request.session = {}

        html = tpl.render(Context({'request': request}))
        self.assertTrue(len(html) > 0)
        url = reverse("coop_cms_hide_accept_cookies_message")
        self.assertTrue(html.find(url) > 0)

    def test_view_accept_cookies_messages_hidden(self):
        tpl = Template('{% load coop_utils %}{% show_accept_cookie_message %}')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        request.session = {'hide_accept_cookie_message': True}

        html = tpl.render(Context({'request': request}))
        self.assertTrue(len(html) == 0)

    def test_view_accept_cookies_custom_template(self):
        tpl = Template('{% load coop_utils %}{% show_accept_cookie_message "test/_accept_cookies_message.html" %}')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        request.session = {}

        html = tpl.render(Context({'request': request}))
        self.assertEqual(html, "Accept cookies")
