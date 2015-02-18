# -*- coding: utf-8 -*-
"""unitesting of templatetags"""

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
from coop_cms.templatetags.coop_utils import get_part, get_parts, group_in_sublists, find_css
from coop_cms.tests import BaseTestCase


class CmsEditTagTest(BaseTestCase):
    """Cms templatetags"""

    def setUp(self):
        super(CmsEditTagTest, self).setUp()
        self.user = None
        self.link1 = Link.objects.create(url='http://www.google.fr')
        self.tree = tree = get_navtree_class().objects.create()
        NavNode.objects.create(tree=tree, label=self.link1.url, content_object=self.link1, ordering=1, parent=None)

    def _log_as_editor(self):
        """login with user with edition permissions"""
        user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        self.user = user

        content_type = ContentType.objects.get_for_model(get_article_class())

        perm = 'change_{0}'.format(content_type.model)
        can_edit_article = Permission.objects.get(content_type=content_type, codename=perm)
        user.user_permissions.add(can_edit_article)

        perm = 'add_{0}'.format(content_type.model)
        can_add_article = Permission.objects.get(content_type=content_type, codename=perm)
        user.user_permissions.add(can_add_article)

        user.is_active = True
        user.save()

        return self.client.login(username='toto', password='toto')

    def _create_article(self):
        """create an article"""
        article_class = get_article_class()
        article = article_class.objects.create(
            title='test', content='<h1>Ceci est un test</h1>',
            publication=BaseArticle.PUBLISHED,
            template="test/nav_tag_in_edit_tag.html"
        )
        NavNode.objects.create(tree=self.tree, label=article.title, content_object=article, ordering=1, parent=None)
        return article

    def test_nav_in_cms_edit_tag_on_view(self):
        """test navigation in cms_edit template tag is displayed properly"""
        article = self._create_article()

        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)

        #text in template
        self.assertContains(response, "Hello")
        self.assertContains(response, article.content)
        self.assertContains(response, self.link1.url)

    def test_nav_in_cms_edit_tag_on_edit(self):
        """test navigation in cms_edit template tag is displayed properly in edit_mode"""
        self._log_as_editor()
        article = self._create_article()

        response = self.client.get(article.get_edit_url(), follow=True)
        self.assertEqual(200, response.status_code)

        self.assertContains(response, "Hello")
        self.assertContains(response, article.content)
        self.assertContains(response, self.link1.url)


class ArticleTemplateTagsTest(BaseTestCase):
    """Tes article related tags"""

    def _request(self):
        """return a request"""

        class DummyRequest(object):
            """a dummy request"""

            def __init__(self):
                """constructor"""
                self.LANGUAGE_CODE = settings.LANGUAGES[0][0] # pylint: disable=C0103

        return DummyRequest()

    def test_link_new(self):
        """text article_link tag when article doesn't exist"""
        tpl = Template('{% load coop_utils %}{% article_link "test" %}')
        tpl.render(Context({'request': self._request()}))

        article_class = get_article_class()
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertEqual(article.slug, "test")

    def test_link_existing(self):
        """text article_link tag when article exists"""

        article_class = get_article_class()

        article_class.objects.create(slug="test", title="Test")

        tpl = Template('{% load coop_utils %}{% article_link "test" %}')
        tpl.render(Context({'request': self._request()}))

        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertEqual(article.slug, "test")

    @skipIf(len(settings.LANGUAGES) == 0, "not languages")
    def test_link_language(self):
        """text article_link tag when article in multi-language mode"""

        lang = settings.LANGUAGES[0][0]

        tpl = Template('{% load coop_utils %}{% article_link "test" '+lang+' %}')
        tpl.render(Context({'request': self._request()}))

        article_class = get_article_class()
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertEqual(article.slug, "test")

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_link_force_lang(self):
        """text article_link tag when language is forced"""

        lang = settings.LANGUAGES[0][0]

        tpl = Template('{% load coop_utils %}{% article_link "test" '+lang+' %}')
        request = self._request()
        request.LANGUAGE_CODE = settings.LANGUAGES[1][0]
        tpl.render(Context({'request': request}))

        article_class = get_article_class()
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertEqual(article.slug, "test")

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_link_existing_force_lang(self):
        """text article_link tag when article exists and language is forced"""

        article_class = get_article_class()

        article = article_class.objects.create(slug="test", title="Test")

        request = self._request()
        lang = request.LANGUAGE_CODE = settings.LANGUAGES[1][0]

        setattr(article, "slug_"+lang, "test_"+lang)
        article.save()

        tpl = Template('{% load coop_utils %}{% article_link "test" '+lang+' %}')
        tpl.render(Context({'request': request}))

        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertEqual(article.slug, "test")
        self.assertEqual(getattr(article, "slug_"+lang), "test_"+lang)

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_link_existing_force_default_lang(self):
        """text article_link tag when language is forced to default"""

        article_class = get_article_class()

        article = article_class.objects.create(title="Test")

        request = self._request()
        def_lang = settings.LANGUAGES[0][0]
        cur_lang = request.LANGUAGE_CODE = settings.LANGUAGES[1][0]

        #activate(cur_lang)
        setattr(article, "slug_"+cur_lang, "test_"+cur_lang)
        article.save()

        count = article_class.objects.count()

        tpl = Template('{% load coop_utils %}{% article_link "test" '+def_lang+' %}')
        tpl.render(Context({'request': request}))

        self.assertEqual(article_class.objects.count(), count)
        article = article_class.objects.get(id=article.id)
        self.assertEqual(article.slug, "test")
        self.assertEqual(getattr(article, "slug_"+cur_lang), "test_"+cur_lang)


class PartitionTemplateFilterTest(TestCase):
    """test get_part template tags"""

    def test_get_part_exact(self):
        """when parts of same sizes"""
        objs = range(9)
        self.assertEqual([0, 1, 2], get_part(objs, "1/3"))
        self.assertEqual([3, 4, 5], get_part(objs, "2/3"))
        self.assertEqual([6, 7, 8], get_part(objs, "3/3"))
    
    def test_get_part_inexact(self):
        """when parts of different sizes"""
        objs = range(10)
        self.assertEqual([0, 1, 2, 3], get_part(objs, "1/3"))
        self.assertEqual([4, 5, 6], get_part(objs, "2/3"))
        self.assertEqual([7, 8, 9], get_part(objs, "3/3"))
        
    def test_get_part_empty(self):
        """when empty"""
        objs = []
        self.assertEqual([], get_part(objs, "1/3"))
        self.assertEqual([], get_part(objs, "2/3"))
        self.assertEqual([], get_part(objs, "3/3"))
    
    def test_get_part_less_than(self):
        """when less than required for 1"""
        objs = [0, 1]
        self.assertEqual([0], get_part(objs, "1/3"))
        self.assertEqual([1], get_part(objs, "2/3"))
        self.assertEqual([], get_part(objs, "3/3"))
        
    def test_get_parts_exact(self):
        """parts when same sizes"""
        objs = range(9)
        self.assertEqual([[0, 1, 2], [3, 4, 5], [6, 7, 8]], get_parts(objs, 3))
        
    def test_get_parts_inexact(self):
        """parts when different sizes"""
        objs = range(10)
        self.assertEqual([[0, 1, 2, 3], [4, 5, 6,], [7, 8, 9]], get_parts(objs, 3))

    def test_get_parts_empty(self):
        """parts when empty"""
        objs = []
        self.assertEqual([[], [], []], get_parts(objs, 3))
    
    def test_get_parts_less_than(self):
        """parts when less than required for 1"""
        objs = [0, 1]
        self.assertEqual([[0], [1], []], get_parts(objs, 3))


class AcceptCookieMessageTest(BaseTestCase):
    """Test coop_cms_hide_accept_cookies_message template tag"""

    def test_get_hide_accept_cookies(self):
        """check that hide_accept_cookie requires a POST"""
        url = reverse("coop_cms_hide_accept_cookies_message")
        response = self.client.get(url)

        self.assertEqual(404, response.status_code)

        self.assertEqual(self.client.session.get('hide_accept_cookie_message', None), None)

    def test_post_hide_accept_cookies(self):
        """check hide message request"""

        url = reverse("coop_cms_hide_accept_cookies_message")
        response = self.client.post(url)

        self.assertEqual(200, response.status_code)

        json_content = json.loads(response.content)
        self.assertEqual(json_content["Ok"], True)

        self.assertEqual(self.client.session.get('hide_accept_cookie_message'), True)

    def test_view_accept_cookies_message(self):
        """check accept_cookie is shown if not accepted"""
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
        """check accept_cookie is hidden if accepted"""
        tpl = Template('{% load coop_utils %}{% show_accept_cookie_message %}')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        request.session = {'hide_accept_cookie_message': True}

        html = tpl.render(Context({'request': request}))
        self.assertTrue(len(html) == 0)

    def test_view_accept_cookies_custom_template(self):
        """check that it is possible to provide a custom template for the message"""
        tpl = Template('{% load coop_utils %}{% show_accept_cookie_message "test/_accept_cookies_message.html" %}')

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        request.session = {}

        html = tpl.render(Context({'request': request}))
        self.assertEqual(html, "Accept cookies")


class GroupInSublistsTest(TestCase):
    """test group_in_sublists template tags"""

    def test_group_in_sublists_empty(self):
        """when empty"""
        self.assertEqual([], group_in_sublists([], 3))

    def test_group_in_sublists_exact(self):
        """when sublist of same size"""
        self.assertEqual([[1, 2], [3, 4]], group_in_sublists([1, 2, 3, 4], 2))

    def test_group_in_sublists_not_exact(self):
        """when sublists of different sizes"""
        self.assertEqual([[1, 2], [3, 4], [5]], group_in_sublists([1, 2, 3, 4, 5], 2))

    def test_group_in_sublists_exact_only_1(self):
        """when only 1 full sublist"""
        self.assertEqual([[1, 2, 3, 4]], group_in_sublists([1, 2, 3, 4], 4))

    def test_group_in_sublists_not_exact_only_1(self):
        """when only 1 not-full sublist"""
        self.assertEqual([[1, 2, 3, 4, 5]], group_in_sublists([1, 2, 3, 4, 5], 6))


class FindCssTestCase(TestCase):
    """find_css template tag"""

    def test_find_css_one(self):
        """check template filter returns true if in css_classes : equal to css_classes"""
        self.assertTrue(find_css("col1", "col1"))

    def test_find_css_several(self):
        """check template filter returns true if in css_classes: in css_classes"""
        self.assertTrue(find_css("col1 ligne", "col1"))
        self.assertTrue(find_css("col1 ligne", "ligne"))

    def test_dont_find(self):
        """check template filter returns false if different"""
        self.assertFalse(find_css("col1", "col2"))

    def test_dont_find_several(self):
        """check template filter returns false if not in css_classes"""
        self.assertFalse(find_css("col1 ligne", "col2"))
