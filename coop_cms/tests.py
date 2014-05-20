# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()
    
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Template, Context
from coop_cms.models import Link, NavNode, NavType, Document, Newsletter, NewsletterItem, Fragment, FragmentType, FragmentFilter
from coop_cms.models import PieceOfHtml, NewsletterSending, BaseArticle, ArticleCategory, Alias
from coop_cms.settings import is_localized, is_multilang
import json
from django.core.exceptions import ValidationError
from coop_cms.settings import get_article_class, get_article_templates, get_navtree_class, is_perm_middleware_installed
from model_mommy import mommy
from django.conf import settings
import os.path, shutil
from django.core.files import File
from django.core import mail
from coop_cms.html2text import html2text
from coop_cms.utils import make_links_absolute
from datetime import datetime, timedelta
from django.core import management
from django.utils import timezone
from django.contrib.sites.models import Site
from coop_cms.apps.test_app.tests import GenericViewTestCase as BaseGenericViewTestCase
from bs4 import BeautifulSoup
import logging
from django.utils.translation import activate, get_language
from unittest import skipIf
#from django.core.files.uploadedfile import SimpleUploadedFile

try:
    AUTH_LOGIN_NAME = "auth_login"
    reverse(AUTH_LOGIN_NAME)
except:
    AUTH_LOGIN_NAME = "login"

class BaseTestCase(TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        
    def tearDown(self):
        logging.disable(logging.NOTSET)

def make_dt(dt):
    if settings.USE_TZ:
        return timezone.make_aware(dt, timezone.get_default_timezone())
    else:
        return dt
    
class BaseArticleTest(BaseTestCase):
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
    
    def _log_as_staff_editor(self):
        self._log_as_editor()
        self.user.is_staff = True
        self.user.save()
    
    def _log_as_non_editor(self):
        self.regular_user = user = User.objects.create_user('zozo', 'zozo@toto.fr', 'zozo')
        
        user.is_active = True
        user.save()
        return self.client.login(username='zozo', password='zozo')
        
    def _log_as_editor_no_add(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)
        
        user.is_active = True
        user.save()
        
        return self.client.login(username='toto', password='toto')
    
class ArticleTest(BaseArticleTest):
    
    def setUp(self):
        super(ArticleTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        
    def tearDown(self):
        super(ArticleTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates
        
    

    def _check_article(self, response, data):
        for (key, value) in data.items():
            self.assertContains(response, value)
            
    def _check_article_not_changed(self, article, data, initial_data):
        article = get_article_class().objects.get(id=article.id)

        for (key, value) in data.items():
            self.assertNotEquals(getattr(article, key), value)
            
        for (key, value) in initial_data.items():
            self.assertEquals(getattr(article, key), value)

    def test_view_article(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        self.assertEqual(article.slug, 'test')
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_publication_flag_published(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        self.assertEqual(article.is_draft(), False)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_publication_flag_draft(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.DRAFT)
        self.assertEqual(article.is_draft(), True)
        url = article.get_absolute_url()
        response = self.client.get(url)
        if is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
    def test_404_ok(self):
        response = self.client.get("/jhjhjkahekhj", follow=True)
        self.assertEqual(404, response.status_code)
        
    def test_is_navigable(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        if is_localized():
            lang = settings.LANGUAGES[0][0]
            self.assertEqual('/{0}/test/'.format(lang), article.get_absolute_url())
        else:
            self.assertEqual('/test/', article.get_absolute_url())

    def test_create_slug(self):
        article = get_article_class().objects.create(title=u"voici l'été", publication=BaseArticle.PUBLISHED)
        self.assertEqual(article.slug, 'voici-lete')
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_edit_article(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        
        data = {"title": 'salut', 'content': 'bonjour!'}
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
        data = {"title": 'bye', 'content': 'au revoir'}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
    def test_article_edition_permission(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        url = article.get_edit_url()
        data = {"title": 'salut', "content": 'oups'}
        response = self.client.post(url, data=data)
        if is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEquals(article.title, initial_data['title'])
        self.assertEquals(article.content, initial_data['content'])
        
    def _is_aloha_found(self, response):
        self.assertEqual(200, response.status_code)
        aloha_js = reverse('aloha_init')
        content = unicode(response.content, 'utf-8')
        return (content.find(aloha_js)>0)
        
    def test_edit_permission(self):
        initial_data = {'title': "ceci est un test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        response = self.client.get(article.get_absolute_url(), follow=True)
        self.assertEqual(200, response.status_code)
        
        url = article.get_edit_url()
        response = self.client.get(url, follow=False)
        if is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
    
        self._log_as_editor()
        response = self.client.get(article.get_edit_url(), follow=False)#follow was TRue?
        self.assertEqual(200, response.status_code)
        
    def test_aloha_loaded(self):
        initial_data = {'title': u"ceci est un test", 'content': u"this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        response = self.client.get(article.get_absolute_url())
        self.assertFalse(self._is_aloha_found(response))
        
        self._log_as_editor()
        response = self.client.get(article.get_edit_url())
        self.assertTrue(self._is_aloha_found(response))
        
    def test_aloha_links(self):
        slugs = ("un", "deux", "trois", "quatre")
        for slug in slugs:
            get_article_class().objects.create(publication=BaseArticle.PUBLISHED, title=slug)
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(**initial_data)
        
        self._log_as_editor()
        response = self.client.get(reverse('aloha_init'))
        
        context_slugs = [article.slug for article in response.context['links']]
        for slug in slugs:
            self.assertTrue(slug in context_slugs)
        
    def test_view_draft_article(self):
        self.client.logout()
        article = get_article_class().objects.create(title="test", publication=BaseArticle.DRAFT)
        url = article.get_absolute_url()
        response = self.client.get(url)
        if is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
        self._log_as_editor()
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_accept_regular_html(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        html = '<h1>paul</h1><a href="/" target="_blank">georges</a><p><b>ringo</b></p>'
        html += '<h6>john</h6><img src="/img.jpg"><br><table><tr><th>A</th><td>B</td></tr>'
        data = {'content': html, 'title': 'ok'}
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=False)
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        #checking html content would not work. Check that the article is updated
        for b in ['paul', 'georges', 'ringo', 'john']:
            self.assertContains(response, b)
        
    #def test_no_malicious_when_editing(self):
    #    initial_data = {'title': "test", 'content': "this is my article content"}
    #    article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
    #    
    #    data1 = {'content': "<script>alert('aahhh');</script>", 'title': 'ok'}
    #    data2 = {'title': '<a href="/">home</a>', 'content': 'ok'}
    #    
    #    self._log_as_editor()
    #    response = self.client.post(article.get_edit_url(), data=data1, follow=True)
    #    self.assertEqual(response.status_code, 200)
    #    self._check_article_not_changed(article, data1, initial_data)
    #    
    #    response = self.client.post(article.get_edit_url(), data=data2, follow=True)
    #    self.assertEqual(response.status_code, 200)
    #    self._check_article_not_changed(article, data2, initial_data)
        
    def test_publish_article(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.DRAFT, **initial_data)
        
        self._log_as_editor()
        
        data = {
            'publication': BaseArticle.PUBLISHED,
        }
        
        response = self.client.post(article.get_publish_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, BaseArticle.PUBLISHED)

    def test_draft_article(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        
        self._log_as_editor()
        
        data = {
            'publication': BaseArticle.DRAFT,
        }
        
        response = self.client.post(article.get_publish_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, BaseArticle.DRAFT)
        
    def test_new_article(self):
        Article = get_article_class()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        
        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.publication, data['publication'])
        self.assertEqual(article.template, data['template'])
        self.assertEqual(article.navigation_parent, None)
        self.assertEqual(NavNode.objects.count(), 0)
        
    def test_new_article_published(self):
        Article = get_article_class()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        
        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.publication, data['publication'])
        self.assertEqual(article.template, data['template'])
        self.assertEqual(article.navigation_parent, None)
        self.assertEqual(NavNode.objects.count(), 0)
        
    def test_new_article_anonymous(self):
        Article = get_article_class()
        
        self._log_as_editor() #create self.user
        self.client.logout()
        data = {
            'title': "Ceci est un titre",
            'publication': BaseArticle.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(200, response.status_code) #if can_edit returns 404 error
        next_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(login_url in next_url)
        
        self.assertEqual(Article.objects.filter(title=data['title']).count(), 0)
        
    def test_new_article_no_perm(self):
        Article = get_article_class()
        
        self._log_as_editor_no_add()
        data = {
            'title': "Ceci est un titre",
            'publication': BaseArticle.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertEqual(Article.objects.filter(title=data['title']).count(), 0)
        
    def test_new_article_navigation(self):
        Article = get_article_class()
        
        tree = get_navtree_class().objects.create()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': -tree.id,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        
        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.publication, data['publication'])
        self.assertEqual(article.template, data['template'])
        self.assertEqual(article.navigation_parent, -tree.id)
        
        self.assertEqual(NavNode.objects.count(), 1)
        node = NavNode.objects.all()[0]
        self.assertEqual(node.content_object, article)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.tree, tree)
        
    def test_new_article_navigation_leaf(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        Article = get_article_class()
        art1 = Article.objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        
        tree = get_navtree_class().objects.create()
        ct = ContentType.objects.get_for_model(Article)
        node1 = NavNode.objects.create(content_type=ct, object_id=art1.id, tree=tree, parent=None)
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': node1.id,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.exclude(id=art1.id).count(), 1)
        art2 = Article.objects.exclude(id=art1.id)[0]
        
        self.assertEqual(art2.title, data['title'])
        self.assertEqual(art2.publication, data['publication'])
        self.assertEqual(art2.template, data['template'])
        self.assertEqual(art2.navigation_parent, node1.id)
        
        self.assertEqual(NavNode.objects.count(), 2)
        node2 = NavNode.objects.exclude(id=node1.id)[0]
        self.assertEqual(node2.content_object, art2)
        self.assertEqual(node2.parent, node1)
        
    def test_article_settings(self, move_nav=False):
        initial_data = {'title': "test", 'content': "this is my article content"}
        Article = get_article_class()
        art0 = mommy.make(Article)
        
        art1 = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        
        tree = get_navtree_class().objects.create()
        ct = ContentType.objects.get_for_model(Article)
        node1 = NavNode.objects.create(content_type=ct, object_id=art0.id, tree=tree, parent=None)
        node2 = NavNode.objects.create(content_type=ct, object_id=art0.id, tree=tree, parent=None)
        
        category = mommy.make(ArticleCategory)
        
        self._log_as_editor()
        data = {
            'template': get_article_templates(None, self.user)[0][0],
            'category': category.id,
            'publication': BaseArticle.PUBLISHED,
            'publication_date': "2013-01-01 12:00:00",
            'headline': True,
            'in_newsletter': True,
            'summary': 'short summary',
            'navigation_parent': node1.id,
        }
        
        response = self.client.post(reverse('coop_cms_article_settings', args=[art1.id]), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.exclude(id__in=(art1.id, art0.id)).count(), 0)
        art1 = Article.objects.get(id=art1.id)
        
        self.assertEqual(art1.title, initial_data['title'])
        self.assertEqual(art1.publication, data['publication'])
        self.assertEqual(art1.navigation_parent, node1.id)
        self.assertEqual(art1.publication_date, make_dt(datetime(2013, 1, 1, 12, 0, 0)))
        self.assertEqual(art1.headline, data['headline'])
        self.assertEqual(art1.in_newsletter, data['in_newsletter'])
        self.assertEqual(art1.summary, data['summary'])
        self.assertEqual(art1.template, data['template'])
        
        self.assertEqual(NavNode.objects.count(), 3)
        node = NavNode.objects.exclude(id__in=(node1.id, node2.id))[0]
        self.assertEqual(node.content_object, art1)
        self.assertEqual(node.parent, node1)
        
        #Update the article
        category2 = mommy.make(ArticleCategory)
        
        node_id = node2.id if move_nav else node1.id
        
        data = {
            'template': get_article_templates(None, self.user)[1][0],
            'category': category2.id,
            'publication': BaseArticle.DRAFT,
            'publication_date': "2013-01-01 18:00:00",
            'headline': False,
            'in_newsletter': False,
            'summary': 'another summary',
            'navigation_parent': node_id,
        }
        
        response = self.client.post(reverse('coop_cms_article_settings', args=[art1.id]), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.exclude(id__in=(art1.id, art0.id)).count(), 0)
        art1 = Article.objects.get(id=art1.id)
        
        self.assertEqual(art1.title, initial_data['title'])
        self.assertEqual(art1.publication, data['publication'])
        self.assertEqual(art1.template, data['template'])
        self.assertEqual(art1.publication_date, make_dt(datetime(2013, 1, 1, 18, 0, 0)))
        self.assertEqual(art1.headline, data['headline'])
        self.assertEqual(art1.in_newsletter, data['in_newsletter'])
        self.assertEqual(art1.summary, data['summary'])
        #self.assertEqual(art1.navigation_parent, data['navigation_parent'])
        
        if move_nav:
            self.assertEqual(NavNode.objects.count(), 4)
            node = NavNode.objects.exclude(id__in=(node1.id, node2.id, node.id))[0]
            self.assertEqual(node.content_object, art1)
            self.assertEqual(node.parent, node2)
        else:
            self.assertEqual(NavNode.objects.count(), 3)
            node = NavNode.objects.exclude(id__in=(node1.id, node2.id))[0]
            self.assertEqual(node.content_object, art1)
            self.assertEqual(node.parent, node1)
            
    def test_article_settings_move_nav(self):
        self.test_article_settings(True)

class TemplateTest(BaseArticleTest):
    
    def setUp(self):
        super(TemplateTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('coop_cms/article.html', 'coop_cms base article'),
            ('test/article.html', 'test article'),
        )
        
    def tearDown(self):
        super(TemplateTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates

    def test_view_article(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertTemplateUsed(response, 'coop_cms/article.html')
        self.assertEqual(200, response.status_code)
        
    def test_view_article_custom_template(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.PUBLISHED, template='test/article.html')
        response = self.client.get(article.get_absolute_url())
        self.assertTemplateUsed(response, 'test/article.html')
        self.assertEqual(200, response.status_code)
        
    def test_change_template(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass)
        self._log_as_editor()
        url = reverse('coop_cms_change_template', args=[article.id])
        response = self.client.post(url, data={'template': 'test/article.html'}, follow=True)
        self.assertEqual(200, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.template, 'test/article.html')
        
    def test_change_template_permission(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass)
        url = reverse('coop_cms_change_template', args=[article.id])
        response = self.client.post(url, data={'template': 'test/article.html'}, follow=True)
        self.assertEqual(200, response.status_code)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.template, '')

class NavigationTest(BaseTestCase):

    def setUp(self):
        super(NavigationTest, self).setUp()
        self.url_ct = ContentType.objects.get(app_label='coop_cms', model='link')
        NavType.objects.create(content_type=self.url_ct, search_field='url', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        self.editor = None
        self.staff = None
        self.tree = get_navtree_class().objects.create()
        self.srv_url = reverse("navigation_tree", args=[self.tree.id])

    def _log_as_editor(self):
        if not self.editor:
            self.editor = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
            self.editor.is_staff = True
            tree_class = get_navtree_class()
            can_edit_tree = Permission.objects.get(
                content_type__app_label=tree_class._meta.app_label,
                codename='change_{0}'.format(tree_class._meta.module_name)
            )
            self.editor.user_permissions.add(can_edit_tree)
            self.editor.is_active
            self.editor.save()
        
        return self.client.login(username='toto', password='toto')
        
    def _log_as_staff(self):
        if not self.staff:
            self.staff = User.objects.create_user('titi', 'titi@titi.fr', 'titi')
            self.staff.is_staff = True
            self.staff.is_active = True
            self.staff.save()
        
        self.client.login(username='titi', password='titi')

    def test_view_in_admin(self):
        self._log_as_editor()
        tree_class = get_navtree_class()
        
        reverse_name = "admin:{0}_{1}_changelist".format(tree_class._meta.app_label, tree_class._meta.module_name)
        url = reverse(reverse_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        reverse_name = "admin:{0}_{1}_change".format(tree_class._meta.app_label, tree_class._meta.module_name)
        tree = tree_class.objects.create(name='another_tree')
        url = reverse(reverse_name, args=[tree.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_add_node(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.google.fr')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
        #Add a second node as child
        link2 = Link.objects.create(url="http://www.python.org")
        data['object_id'] = link2.id
        data['parent_id'] = nav_node.id
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.python.org')
        nav_node2 = NavNode.objects.get(object_id=link2.id, content_type=self.url_ct)
        self.assertEqual(nav_node2.label, 'http://www.python.org')
        self.assertEqual(nav_node2.content_object, link2)
        self.assertEqual(nav_node2.parent, nav_node)
        self.assertEqual(nav_node.ordering, 1)
        
    def test_add_node_twice(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.google.fr')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
        #Add a the same object a 2nd time
        data['object_id'] = link.id
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
    def test_move_node_to_parent(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[-2].id,
            'parent_id': nodes[0].id,
            'ref_pos': 'after',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[-2].id)
        self.assertEqual(node.parent, nodes[0])
        self.assertEqual(node.ordering, 1)
        
        root_nodes = [node for node in NavNode.objects.filter(parent__isnull=True).order_by("ordering")]
        self.assertEqual(nodes[:-2]+nodes[-1:], root_nodes)
        self.assertEqual([1, 2, 3], [n.ordering for n in root_nodes])
        
    def test_move_node_to_root(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.toto.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        nodes[1].parent = nodes[0]
        nodes[1].ordering = 1
        nodes[1].save()
        nodes[2].parent = nodes[0]
        nodes[2].ordering = 2
        nodes[2].save()
        
        self._log_as_editor()
        
        #Move after
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[1].id,
            'ref_pos': 'after',
            'ref_id': nodes[0].id,            
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[1].id)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.ordering, 2)
        self.assertEqual(NavNode.objects.get(id=nodes[0].id).ordering, 1)
        self.assertEqual(NavNode.objects.get(id=nodes[2].id).ordering, 1)
        
        #Move before
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[2].id,
            'ref_pos': 'before',
            'ref_id': nodes[0].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        #if result['status'] != 'success':
        #    print result['message']
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[2].id)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.ordering, 1)
        self.assertEqual(NavNode.objects.get(id=nodes[0].id).ordering, 2)
        self.assertEqual(NavNode.objects.get(id=nodes[1].id).ordering, 3)
        
    def test_move_same_level(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #Move the 4th just after the 1st one
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[-2].id,
            'ref_id': nodes[0].id,
            'ref_pos': 'after',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        nodes = [NavNode.objects.get(id=n.id) for n in nodes]#refresh
        [self.assertEqual(n.parent, None) for n in nodes]
        self.assertEqual([1, 3, 2, 4], [n.ordering for n in nodes])
        
        #Move the 1st before the 4th
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[0].id,
            'ref_id': nodes[-1].id,
            'ref_pos': 'before',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        nodes = [NavNode.objects.get(id=n.id) for n in nodes]#refresh
        [self.assertEqual(n.parent, None) for n in nodes]
        self.assertEqual([3, 2, 1, 4], [n.ordering for n in nodes])
        
    def test_delete_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': nodes[1].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        nodes_after = NavNode.objects.all().order_by('ordering')
        self.assertEqual(3, len(nodes_after))
        self.assertTrue(nodes[1] not in nodes_after)
        for i, node in enumerate(nodes_after):
            self.assertTrue(node in nodes)
            self.assertTrue(i+1, node.ordering)
            
    def test_delete_node_and_children(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        nodes[-1].parent = nodes[-2]
        nodes[-1].ordering = 1
        nodes[-1].save()
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': nodes[-2].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        nodes_after = NavNode.objects.all().order_by('ordering')
        self.assertEqual(2, len(nodes_after))
        self.assertTrue(nodes[-1] not in nodes_after)
        self.assertTrue(nodes[-2] not in nodes_after)
        for i, node in enumerate(nodes_after):
            self.assertTrue(node in nodes)
            self.assertTrue(i+1, node.ordering)
            
    def test_rename_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #rename the 1st one
        data = {
            'msg_id': 'rename_navnode',
            'node_id': nodes[0].id,
            'name': 'Google',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        node = NavNode.objects.get(id=nodes[0].id)
        self.assertEqual(data["name"], node.label)
        self.assertEqual(links[0].url, node.content_object.url)#object not renamed
        
        for n in nodes[1:]:
            node = NavNode.objects.get(id=n.id)
            self.assertEqual(n.label, node.label)
        
    def test_view_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'view_navnode',
            'node_id': nodes[0].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['html'].find(nodes[0].get_absolute_url())>=0)
        self.assertTrue(result['html'].find(nodes[1].get_absolute_url())<0)
        self.assertTemplateUsed(response, 'coop_cms/navtree_content/default.html')
        
    def _do_test_get_suggest_list(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a, title=a) for a in addrs]
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': '.fr'
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 4) #3 + noeud vide
        
    def test_get_suggest_list(self):
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_get_label(self):
        
        nt = NavType.objects.get(content_type=self.url_ct)
        nt.search_field = ''
        nt.label_rule=NavType.LABEL_USE_GET_LABEL
        nt.save()
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_unicode(self):
        
        nt = NavType.objects.get(content_type=self.url_ct)
        nt.search_field = ''
        nt.label_rule=NavType.LABEL_USE_UNICODE
        nt.save()
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_only_not_in_navigation(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a, title=a) for a in addrs]
        
        link = links[0]
        node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None)
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': '.fr'
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 3) #2 + noeud vide
        
    def test_get_suggest_empty_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': 'python'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 1)
        self.assertEqual(result['suggestions'][0]['value'], 0)
        self.assertEqual(result['suggestions'][0]['type'], '')
        
    def test_get_suggest_tree_type_all(self):
        nt_link = NavType.objects.get(content_type=self.url_ct)
        
        ct = ContentType.objects.get_for_model(get_article_class())
        nt_art = NavType.objects.create(content_type=ct, search_field='title', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        self.assertEqual(self.tree.types.count(), 0)
        
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a, title=a) for a in addrs]
        
        article = get_article_class().objects.create(title="python", content='nice snake')
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': 'python'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 3) #2 + noeud vide

    def test_get_suggest_tree_type_filter(self):
        nt_link = NavType.objects.get(content_type=self.url_ct)
        
        ct = ContentType.objects.get_for_model(get_article_class())
        nt_art = NavType.objects.create(content_type=ct, search_field='title', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        self.tree.types.add(nt_art)
        self.tree.save()
        
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a, title=a) for a in addrs]
        
        article = get_article_class().objects.create(title="python", content='nice snake')
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': 'python'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 2) #1 + noeud vide
        self.assertEqual(result['suggestions'][0]['label'], 'python')
        
    def test_unknow_message(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'oups',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_missing_message(self):
        self._log_as_editor()
        
        data = {
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        
    def test_not_ajax(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        
        response = self.client.post(self.srv_url, data=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(0, NavNode.objects.count())
        
    def test_add_unknown_obj(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': 11,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(0, NavNode.objects.count())
        
    def test_remove_unknown_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': 11,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_rename_unknown_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'remove_navnode',
            'node_id': 11,
            'label': 'oups'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_check_auth(self):
        link = Link.objects.create(url='http://www.google.fr')
        
        for msg_id in ('add_navnode', 'move_navnode', 'rename_navnode', 'get_suggest_list', 'view_navnode', 'remove_navnode'):
            data = {
                'ref_pos': 'after',
                'name': 'oups',
                'term': 'goo',
                'object_type':'coop_cms.link',
                'object_id': link.id,
                'msg_id': msg_id
            }
            if msg_id != 'add_navnode':
                node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None)
                data.update({'node_id': node.id, 'node_ids': node.id})
            
            self._log_as_staff()
            response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertEqual(result['status'], 'error')
            
            self._log_as_editor()
            response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertEqual(result['status'], 'success')
            
            NavNode.objects.all().delete()
            
    def test_set_out_of_nav(self):
        self._log_as_editor()
        
        link = Link.objects.create(url='http://www.google.fr')
        node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None, in_navigation=True)
        
        data = {
            'msg_id': 'navnode_in_navigation',
            'node_id': node.id,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertNotEqual(result['message'], '')
        self.assertEqual(result['icon'], 'out_nav')
        node = NavNode.objects.get(id=node.id)
        self.assertFalse(node.in_navigation)
        
    def test_set_in_nav(self):
        self._log_as_editor()
        
        link = Link.objects.create(url='http://www.google.fr')
        node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None, in_navigation=False)
        
        data = {
            'msg_id': 'navnode_in_navigation',
            'node_id': node.id,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertNotEqual(result['message'], '')
        self.assertEqual(result['icon'], 'in_nav')
        node = NavNode.objects.get(id=node.id)
        self.assertTrue(node.in_navigation)
        
    def test_delete_object(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        parent = None
        for i, link in enumerate(links):
            parent = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=parent)
            
        links[1].delete()
        
        self.assertEqual(0, Link.objects.filter(url=addrs[1]).count())
        for url in addrs[:1]+addrs[2:]:
            self.assertEqual(1, Link.objects.filter(url=url).count())
            
        nodes = NavNode.objects.all()
        self.assertEqual(1, nodes.count())
        node = nodes[0]
        self.assertEqual(addrs[0], node.content_object.url)
        
    def test_delete_article(self):
        Article = get_article_class()
        article1 = mommy.make(Article, title="abcd")
        article2 = mommy.make(Article, title="efgh")
        
        nodes = []
        parent = None
        for i, art in enumerate((article1, article2)):
            node = NavNode.objects.create(
                tree=self.tree, label=art.title, content_object=art, ordering=i+1, parent=None)
            
        article2.delete()
        
        self.assertEqual(1, Article.objects.count())
            
        nodes = NavNode.objects.all()
        self.assertEqual(1, nodes.count())
        node = nodes[0]
        self.assertEqual(article1.get_absolute_url(), node.get_absolute_url())
        
    def test_invalid_node(self):
        Article = get_article_class()
        article = mommy.make(Article, title="abcd")
        
        ct = ContentType.objects.get_for_model(Article)
        
        nodes = []
        parent = None
        node1 = NavNode.objects.create(
            tree=self.tree, label="#LABEL1#", content_type=None, object_id=article.id, ordering=1, parent=None)
        
        node2 = NavNode.objects.create(
            tree=self.tree, label="#LABEL2#", content_type=ct, object_id=0, ordering=1, parent=None)
        
        nodes = NavNode.objects.all()
        self.assertEqual(2, nodes.count())
        self.assertEqual(None, nodes[0].get_absolute_url())
        self.assertEqual(None, nodes[1].get_absolute_url())
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        self.assertTrue(html.find(node1.label)>0)
        self.assertTrue(html.find(node2.label)>0)
        
    def test_delete_parent(self):
        Article = get_article_class()
        article = mommy.make(Article, title="abcd")
        
        ct = ContentType.objects.get_for_model(Article)
        
        nodes = []
        parent = None
        node1 = NavNode.objects.create(
            tree=self.tree, label="#LABEL1#", content_type=None, object_id=article.id, ordering=1, parent=None)
        
        node2 = NavNode.objects.create(
            tree=self.tree, label="#LABEL2#", content_type=ct, object_id=0, ordering=1, parent=None)
        
        nodes = NavNode.objects.all()
        self.assertEqual(2, nodes.count())
        self.assertEqual(None, nodes[0].get_absolute_url())
        self.assertEqual(None, nodes[1].get_absolute_url())
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        self.assertTrue(html.find(node1.label)>0)
        self.assertTrue(html.find(node2.label)>0)
        

class TemplateTagsTest(BaseTestCase):
    
    def setUp(self):
        super(TemplateTagsTest, self).setUp()
        link1 = Link.objects.create(url='http://www.google.fr')
        link2 = Link.objects.create(url='http://www.python.org')
        link3 = Link.objects.create(url='http://www.quinode.fr')
        link4 = Link.objects.create(url='http://www.apidev.fr')
        link5 = Link.objects.create(url='http://www.toto.fr')
        link6 = Link.objects.create(url='http://www.titi.fr')
        
        self.nodes = []
        
        self.tree = tree = get_navtree_class().objects.create()
        
        self.nodes.append(NavNode.objects.create(tree=tree, label=link1.url, content_object=link1, ordering=1, parent=None))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link2.url, content_object=link2, ordering=2, parent=None))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link3.url, content_object=link3, ordering=3, parent=None))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link4.url, content_object=link4, ordering=1, parent=self.nodes[2]))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link5.url, content_object=link5, ordering=1, parent=self.nodes[3]))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link6.url, content_object=link6, ordering=2, parent=self.nodes[3]))
        
    def test_view_navigation(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        positions = [html.find('{0}'.format(n.content_object.url)) for n in self.nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def _insert_new_node(self):
        link7 = Link.objects.create(url='http://www.tutu.fr')
        self.nodes.insert(-1, NavNode.objects.create(tree=self.tree, label=link7.url, content_object=link7, ordering=2, parent=self.nodes[3]))
        self.nodes[-1].ordering = 3
        self.nodes[-1].save()
        
    def test_view_navigation_order(self):
        self._insert_new_node()
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        positions = [html.find('{0}'.format(n.content_object.url)) for n in self.nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_out_of_navigation(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        for n in self.nodes[:2]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[2:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_navigation_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul li_template=cst_tpl%}')
        
        html = tpl.render(Context({'cst_tpl': cst_tpl}))
        
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
    
    def test_navigation_other_tree(self):    
        link1 = Link.objects.create(url='http://www.my-tree.com')
        link2 = Link.objects.create(url='http://www.mon-arbre.fr')
        link3 = Link.objects.create(url='http://www.mon-arbre.eu')
        
        tree = get_navtree_class().objects.create(name="mon_arbre")
        
        n1 = NavNode.objects.create(tree=tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        n2 = NavNode.objects.create(tree=tree, label=link2.url, content_object=link2, ordering=2, parent=None)
        n3 = NavNode.objects.create(tree=tree, label=link3.url, content_object=link3, ordering=2, parent=n2)
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul tree=mon_arbre %}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), 3)
        
        self.assertTrue(html.find(n1.get_absolute_url())>0)
        self.assertTrue(html.find(n2.get_absolute_url())>0)
        self.assertTrue(html.find(n3.get_absolute_url())>0)
        
        self.assertTrue(html.find(self.nodes[0].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[1].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[2].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[3].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[4].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[5].get_absolute_url())<0)
        
    def test_view_navigation_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul li_template=coop_cms/test_li.html%}')
        
        html = tpl.render(Context({}))
        
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
    
    def test_view_navigation_css(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul css_class=toto%}')
        html = tpl.render(Context({}))
        self.assertEqual(html.count('<li class="toto " >'), len(self.nodes))
        
    def test_view_navigation_custom_template_and_css(self):
        tpl = Template(
            '{% load coop_navigation %}{%navigation_as_nested_ul li_template=coop_cms/test_li.html css_class=toto%}'
        )
        html = tpl.render(Context({}))
        self.assertEqual(html.count('<li class="toto " >'), len(self.nodes))
            
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_breadcrumb(self):
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in (self.nodes[0], self.nodes[1], self.nodes[4]) :
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_breadcrumb_out_of_navigation(self):
        for n in self.nodes:
            n.in_navigation = False
            n.save()
        
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in (self.nodes[0], self.nodes[1], self.nodes[4]) :
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)

    def test_view_breadcrumb_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj li_template=cst_tpl%}')
        
        html = tpl.render(Context({'obj': self.nodes[5].content_object, 'cst_tpl': cst_tpl}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_breadcrumb_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj li_template=coop_cms/test_li.html%}')
        
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children(self):
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(n.content_object.url)>=0)
            
        for n in self.nodes[:4]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_children_out_of_navigation(self):
        self.nodes[1].in_navigation = False
        self.nodes[1].save()
        
        self.nodes[5].in_navigation = False
        self.nodes[5].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in (self.nodes[4], ):
            self.assertTrue(html.find(n.content_object.url)>=0)
            
        for n in self.nodes[:4] + [self.nodes[5]]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_children_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{%navigation_children obj  li_template=cst_tpl %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object, 'cst_tpl': cst_tpl}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{%navigation_children obj li_template=coop_cms/test_li.html %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children_order(self):
        self._insert_new_node()
        nodes = self.nodes[3].get_children(in_navigation=True)
        tpl = Template('{% load coop_navigation %}{%navigation_children obj%}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        positions = [html.find(n.content_object.url) for n in nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_siblings(self):
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        for n in self.nodes[:3]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[3:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
    
    def test_view_siblings_order(self):
        self._insert_new_node()
        all_nodes = [n for n in self.nodes]
        nodes = all_nodes[-1].get_siblings(in_navigation=True)
        tpl = Template('{% load coop_navigation %}{%navigation_siblings obj%}')
        html = tpl.render(Context({'obj': all_nodes[-1].content_object}))
        positions = [html.find(n.content_object.url) for n in nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_siblings_out_of_navigation(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        self.nodes[5].in_navigation = False
        self.nodes[5].save()
        
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        
        for n in self.nodes[:2]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[2:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
    
    def test_view_siblings_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj li_template=cst_tpl%}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object, 'cst_tpl': cst_tpl}))
        
        for n in self.nodes[:3]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_siblings_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj li_template=coop_cms/test_li.html%}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        
        for n in self.nodes[:3]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_navigation_no_nodes(self):
        NavNode.objects.all().delete()
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({})).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_breadcrumb_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': link})).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_children_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': link })).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_siblings_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': link})).replace(' ', '')
        self.assertEqual(html, '')
        
    def test_navigation_root_nodes_no_nodes(self):
        NavNode.objects.all().delete()
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes%}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), 0)
        
    def test_navigation_root_nodes(self):
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes%}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), len(self.nodes))
    
    def test_navigation_root_nodes_other_template(self):
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes template_name="test/navigation_node.html" %}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li.test')), len(self.nodes))
        
    def test_navigation_root_nodes_out_of_navigation(self):
        self.nodes[1].in_navigation = False
        self.nodes[1].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes%}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), len(self.nodes)-1)
        
        self.assertTrue(html.find(self.nodes[1].get_absolute_url())<0)
        
    def test_navigation_root_nodes_out_of_navigation_with_child(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes%}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), len(self.nodes)-4)
        
        self.assertTrue(html.find(self.nodes[0].get_absolute_url())>0)
        self.assertTrue(html.find(self.nodes[1].get_absolute_url())>0)
        self.assertTrue(html.find(self.nodes[2].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[3].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[4].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[5].get_absolute_url())<0)
        
    def test_navigation_root_nodes_out_of_navigation_child(self):
        self.nodes[4].in_navigation = False
        self.nodes[4].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes%}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), len(self.nodes)-1)
        
        self.assertTrue(html.find(self.nodes[0].get_absolute_url())>0)
        self.assertTrue(html.find(self.nodes[1].get_absolute_url())>0)
        self.assertTrue(html.find(self.nodes[2].get_absolute_url())>0)
        self.assertTrue(html.find(self.nodes[3].get_absolute_url())>0)
        self.assertTrue(html.find(self.nodes[4].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[5].get_absolute_url())>0)
    
    def test_navigation_root_nodes_other_tree(self):    
        link1 = Link.objects.create(url='http://www.my-tree.com')
        link2 = Link.objects.create(url='http://www.mon-arbre.fr')
        link3 = Link.objects.create(url='http://www.mon-arbre.eu')
        
        tree = get_navtree_class().objects.create(name="mon_arbre")
        
        n1 = NavNode.objects.create(tree=tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        n2 = NavNode.objects.create(tree=tree, label=link2.url, content_object=link2, ordering=2, parent=None)
        n3 = NavNode.objects.create(tree=tree, label=link3.url, content_object=link3, ordering=2, parent=n2)
        
        tpl = Template('{% load coop_navigation %}{%navigation_root_nodes tree=mon_arbre %}')
        html = tpl.render(Context({}))
        soup = BeautifulSoup(html)
        self.assertEqual(len(soup.select('li')), 3)
        
        self.assertTrue(html.find(n1.get_absolute_url())>0)
        self.assertTrue(html.find(n2.get_absolute_url())>0)
        self.assertTrue(html.find(n3.get_absolute_url())>0)
        
        self.assertTrue(html.find(self.nodes[0].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[1].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[2].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[3].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[4].get_absolute_url())<0)
        self.assertTrue(html.find(self.nodes[5].get_absolute_url())<0)
        
        
        
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
        
class DownloadDocTest(BaseTestCase):

    def _clean_files(self):
        dirs = (settings.DOCUMENT_FOLDER, settings.PRIVATE_DOCUMENT_FOLDER)
        for d in dirs:
            try:
                dir_name = '{0}/{1}'.format(settings.MEDIA_ROOT, d)
                shutil.rmtree(dir_name)
            except:
                pass
    
    def setUp(self):
        super(DownloadDocTest, self).setUp()
        settings.DOCUMENT_FOLDER = '_unittest_docs'
        settings.PRIVATE_DOCUMENT_FOLDER = '_unittest_private_docs'
        self._clean_files()
        u = User.objects.create(username='toto')
        u.is_superuser = True
        u.set_password('toto')
        u.save()

    def tearDown(self):
        super(DownloadDocTest, self).tearDown()
        self._clean_files()
        
    def _get_file(self, file_name='unittest1.txt'):
        full_name = os.path.normpath(os.path.dirname(__file__) + '/fixtures/' + file_name)
        return open(full_name, 'rb')
    
    def test_upload_public_doc(self):
        data = {
            'file': self._get_file(),
            'is_private': False,
            'name': 'a test file',
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        public_docs = Document.objects.filter(is_private=False)
        self.assertEquals(1, public_docs.count())
        self.assertEqual(public_docs[0].name, data['name'])
        self.assertEqual(public_docs[0].category, None)
        f = public_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
        
    def test_upload_public_doc_category(self):
        cat = mommy.make(ArticleCategory, name="my cat")
        data = {
            'file': self._get_file(),
            'is_private': False,
            'name': 'a test file',
            'category': cat.id,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        public_docs = Document.objects.filter(is_private=False)
        self.assertEquals(1, public_docs.count())
        self.assertEqual(public_docs[0].name, data['name'])
        self.assertEqual(public_docs[0].category, cat)
        f = public_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
        
    def test_upload_doc_missing_fields(self):
        data = {
            'is_private': False,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())

    def test_upload_doc_anonymous_user(self):
        data = {
            'file': self._get_file(),
            'is_private': False,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)

        
    def test_upload_private_doc(self):
        data = {
            'file': self._get_file(),
            'is_private': True,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        private_docs = Document.objects.filter(is_private=True)
        self.assertEquals(1, private_docs.count())
        self.assertEqual(private_docs[0].name, 'unittest1')
        self.assertEqual(private_docs[0].category, None)
        f = private_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
    
    def test_view_docs(self):
        file1 = File(self._get_file())
        doc1 = mommy.make(Document, is_private=True, file=file1)
        file2 = File(self._get_file())
        doc2 = mommy.make(Document, is_private=False, file=file2)
        
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(reverse('coop_cms_media_documents'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, reverse('coop_cms_download_doc', args=[doc1.id]))
        self.assertNotContains(response, doc1.file.url)
        self.assertNotContains(response, reverse('coop_cms_download_doc', args=[doc2.id]))
        self.assertContains(response, doc2.file.url)
        
    def test_view_docs_anonymous(self):
        response = self.client.get(reverse('coop_cms_media_documents'), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
    
    def test_download_public(self):
        #create a public doc
        file = File(self._get_file())
        doc = mommy.make(Document, is_private=False, file=file)
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertNotEqual(doc.get_download_url(), private_url)
        
        #login and download
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, self._get_file().read())
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self._get_file().read())
        
    @skipIf('sanza.Profile' in settings.INSTALLED_APPS, "sanza.Profile installed")
    def test_download_private(self):
            
        #create a public doc
        file = File(self._get_file())
        cat = mommy.make(ArticleCategory, name="private-doc")
        doc = mommy.make(Document, is_private=True, file=file, category=cat)
            
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertEqual(doc.get_download_url(), private_url)
        
        #login and download
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response['Content-Disposition'], "attachment; filename=unittest1.txt")
        self.assertEquals(response['Content-Type'], "text/plain")
        #TODO: This change I/O Exception in UnitTest
        #self.assertEqual(response.content, self._get_file().read()) 
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        

class UserBaseTestCase(BaseTestCase):

    def setUp(self):
        super(UserBaseTestCase, self).setUp()
        self.editor = None
        self.viewer = None

    def _log_as_editor(self):
        if not self.editor:
            self.editor = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
            self.editor.is_staff = True
            self.editor.is_active = True
            can_edit_newsletter = Permission.objects.get(content_type__app_label='coop_cms', codename='change_newsletter')
            self.editor.user_permissions.add(can_edit_newsletter)
            
            ct = ContentType.objects.get_for_model(get_article_class())
            codename = 'change_{0}'.format(ct.model)
            can_edit_article = Permission.objects.get(content_type__app_label=ct.app_label, codename=codename)
            self.editor.user_permissions.add(can_edit_article)
            self.editor.save()
        
        return self.client.login(username='toto', password='toto')
        
    def _log_as_viewer(self):
        if not self.viewer:
            self.viewer = User.objects.create_user('titi', 'titi@toto.fr', 'titi')
            self.viewer.is_staff = True
            self.viewer.is_active = True
            self.viewer.user_permissions.add(can_edit_newsletter)
            self.viewer.save()
        
        return self.client.login(username='titi', password='titi')

    
    
class NewsletterTest(UserBaseTestCase):

    def test_create_article_for_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art = mommy.make(Article, in_newsletter=True)
        
        self.assertEqual(1, NewsletterItem.objects.count())
        item = NewsletterItem.objects.get(content_type=ct, object_id=art.id)
        self.assertEqual(item.content_object, art)
        
        art.delete()
        self.assertEqual(0, NewsletterItem.objects.count())

    def test_create_article_not_for_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art = mommy.make(Article, in_newsletter=False)
        self.assertEqual(0, NewsletterItem.objects.count())
        
        art.delete()
        self.assertEqual(0, NewsletterItem.objects.count())

    def test_create_article_commands(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        art1 = mommy.make(Article, in_newsletter=True)
        art2 = mommy.make(Article, in_newsletter=True)
        art3 = mommy.make(Article, in_newsletter=False)
        self.assertEqual(2, NewsletterItem.objects.count())
        NewsletterItem.objects.all().delete()
        self.assertEqual(0, NewsletterItem.objects.count())
        management.call_command('create_newsletter_items', verbosity=0, interactive=False)
        self.assertEqual(2, NewsletterItem.objects.count())
        item1 = NewsletterItem.objects.get(content_type=ct, object_id=art1.id)
        item2 = NewsletterItem.objects.get(content_type=ct, object_id=art2.id)

    def test_view_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art1 = mommy.make(Article, title="Art 1", in_newsletter=True)
        art2 = mommy.make(Article, title="Art 2", in_newsletter=True)
        art3 = mommy.make(Article, title="Art 3", in_newsletter=True)
        
        newsletter = mommy.make(Newsletter, content="a little intro for this newsletter",
            template="test/newsletter_blue.html")
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art1.id))
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art2.id))
        newsletter.save()
        
        url = reverse('coop_cms_view_newsletter', args=[newsletter.id])
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, newsletter.content)
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertNotContains(response, art3.title)
        
    def test_edit_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art1 = mommy.make(Article, title="Art 1", in_newsletter=True)
        art2 = mommy.make(Article, title="Art 2", in_newsletter=True)
        art3 = mommy.make(Article, title="Art 3", in_newsletter=True)
        
        newsletter = mommy.make(Newsletter, content="a little intro for this newsletter",
            template="test/newsletter_blue.html")
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art1.id))
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art2.id))
        newsletter.save()
        
        self._log_as_editor()
        url = reverse('coop_cms_edit_newsletter', args=[newsletter.id])
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, newsletter.content)
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertNotContains(response, art3.title)
        
        data = {'content': 'A better intro'}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        self.assertNotContains(response, newsletter.content)
        self.assertContains(response, data['content'])
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertNotContains(response, art3.title)
        
    def test_edit_newsletter_anonymous(self):
        original_data = {'content': "a little intro for this newsletter",
            'template': "test/newsletter_blue.html"}
        newsletter = mommy.make(Newsletter, **original_data)
        
        url = reverse('coop_cms_edit_newsletter', args=[newsletter.id])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        
        response = self.client.post(url, data={'content': ':OP'})
        self.assertEqual(302, response.status_code)
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.content, original_data['content'])
        
    def test_edit_newsletter_no_articles(self):
        self._log_as_editor()
        original_data = {'content': "a little intro for this newsletter",
            'template': "test/newsletter_blue.html"}
        newsletter = mommy.make(Newsletter, **original_data)
        
        url = reverse('coop_cms_edit_newsletter', args=[newsletter.id])
        
        data = {'content': ':OP'}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, data['content'])
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, data['content'])
        
    def test_newsletter_templates(self):
        
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art1 = mommy.make(Article, title="Art 1", in_newsletter=True)
        poh = mommy.make(PieceOfHtml, div_id="newsletter_header", content="HELLO!!!")
        
        newsletter = mommy.make(Newsletter, content="a little intro for this newsletter",
            template="test/newsletter_blue.html")
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art1.id))
        newsletter.save()
        
        self._log_as_editor()
        
        view_names = ['coop_cms_view_newsletter', 'coop_cms_edit_newsletter']
        for view_name in view_names:
            url = reverse(view_name, args=[newsletter.id])
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)
            
            self.assertContains(response, newsletter.content)
            self.assertContains(response, art1.title)
            self.assertContains(response, "background: blue;")
            self.assertNotContains(response, poh.content)
        
        newsletter.template = "test/newsletter_red.html"
        newsletter.save()
        
        for view_name in view_names:
            url = reverse(view_name, args=[newsletter.id])
            response = self.client.get(url)
            
            self.assertEqual(200, response.status_code)
            
            self.assertContains(response, newsletter.content)
            self.assertContains(response, art1.title)
            self.assertContains(response, "background: red;")
            self.assertContains(response, poh.content)
            
    def test_change_newsletter_templates(self):
        settings.COOP_CMS_NEWSLETTER_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        self._log_as_editor()
        
        newsletter = mommy.make(Newsletter, template='test/newsletter_blue.html')
        
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        for tpl, name in settings.COOP_CMS_NEWSLETTER_TEMPLATES:
            self.assertContains(response, tpl)
            self.assertContains(response, name)
            
        data={'template': 'test/newsletter_red.html'}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, reverse('coop_cms_edit_newsletter', args=[newsletter.id]))
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.template, data['template'])
        
    def test_change_newsletter_templates_anonymous(self):
        settings.COOP_CMS_NEWSLETTER_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        original_data={'template': 'test/newsletter_blue.html'}
        newsletter = mommy.make(Newsletter, **original_data)
        
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        
        data={'template': 'test/newsletter_red.html'}
        response = self.client.post(url, data=data)
        self.assertEqual(302, response.status_code)
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.template, original_data['template'])
        
    def test_change_newsletter_unknow_template(self):
        settings.COOP_CMS_NEWSLETTER_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        original_data={'template': 'test/newsletter_blue.html'}
        newsletter = mommy.make(Newsletter, **original_data)
        
        self._log_as_editor()
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        data={'template': 'test/newsletter_yellow.html'}
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.template, original_data['template'])
        
    def test_send_test_newsletter(self, template='test/newsletter_blue.html', extra_checker=None):
        settings.COOP_CMS_FROM_EMAIL = 'contact@toto.fr'
        settings.COOP_CMS_TEST_EMAILS = ('toto@toto.fr', 'titi@toto.fr')
        #settings.COOP_CMS_SITE_PREFIX = 'http://toto.fr'
        settings.SITE_ID = 1
        site = Site.objects.get(id=settings.SITE_ID)
        site.domain = 'toto.fr'
        site.save()
        
        rel_content = u'''
            <h1>Title</h1><a href="{0}/toto/"><img src="{0}/toto.jpg"></a><br /><img src="{0}/toto.jpg">
            <div><a href="http://www.google.fr">Google</a></div>
        '''
        original_data = {
            'template': template,
            'subject': 'test email',
            'content': rel_content.format("")
        }
        newsletter = mommy.make(Newsletter, **original_data)
        
        self._log_as_editor()
        url = reverse('coop_cms_test_newsletter', args=[newsletter.id])
        response = self.client.post(url, data={})
        self.assertEqual(200, response.status_code)
        
        self.assertEqual([[e] for e in settings.COOP_CMS_TEST_EMAILS], [e.to for e in mail.outbox])
        for e in mail.outbox:
            self.assertEqual(e.from_email, settings.COOP_CMS_FROM_EMAIL)
            self.assertEqual(e.subject, newsletter.subject)
            self.assertTrue(e.body.find('Title')>=0)
            self.assertTrue(e.body.find('Google')>=0)
            self.assertTrue(e.alternatives[0][1], "text/html")
            self.assertTrue(e.alternatives[0][0].find('Title')>=0)
            self.assertTrue(e.alternatives[0][0].find('Google')>=0)
            site_prefix = "http://"+site.domain
            self.assertTrue(e.alternatives[0][0].find(site_prefix)>=0)
            if extra_checker:
                extra_checker(e)
        
    def test_schedule_newsletter_sending(self):
        newsletter = mommy.make(Newsletter)
        
        self._log_as_editor()
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        sch_dt = "2030-12-12 12:00:00"
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '$.colorbox.close()')
        self.assertEqual(1, NewsletterSending.objects.count())
        self.assertEqual(newsletter, NewsletterSending.objects.all()[0].newsletter)
        self.assertEqual(2030, NewsletterSending.objects.all()[0].scheduling_dt.year)
        
    def test_schedule_newsletter_sending_invalid_value(self):
        newsletter = mommy.make(Newsletter)
        
        self._log_as_editor()
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        sch_dt = ''
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, NewsletterSending.objects.count())
        
        sch_dt = 'toto'
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, NewsletterSending.objects.count())
        
        sch_dt = "2005-12-12 12:00:00"
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, NewsletterSending.objects.count())
    
    def test_schedule_anonymous(self):
        newsletter = mommy.make(Newsletter)
        
        login_url = reverse('django.contrib.auth.views.login')
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        
        response = self.client.get(url, follow=False)
        redirect_url = response['Location']
        if is_localized():
            login_url = login_url[:2]
            self.assertTrue(redirect_url.find(login_url)>0)
        else:
            self.assertTrue(redirect_url.find(login_url)>0)
        
        sch_dt = timezone.now()+timedelta(1)
        response = self.client.post(url, data={'sending_dt': sch_dt})
        redirect_url = response['Location']
        self.assertTrue(redirect_url.find(login_url)>0)
    
    def test_send_newsletter(self):
        
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello guys!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_blue.html',
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        
        sch_dt = timezone.now() - timedelta(1)
        sending = mommy.make(NewsletterSending, newsletter=newsletter, scheduling_dt= sch_dt, sending_dt= None)
        
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        
        sending = NewsletterSending.objects.get(id=sending.id)
        self.assertNotEqual(sending.sending_dt, None)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['toto@toto.fr'])
        self.assertEqual(email.subject, newsletter_data['subject'])
        self.assertTrue(email.body.find('Hello guys')>=0)
        self.assertTrue(email.alternatives[0][1], "text/html")
        self.assertTrue(email.alternatives[0][0].find('Hello guys')>=0)
        
        #check whet happens if command is called again
        mail.outbox = []
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        self.assertEqual(len(mail.outbox), 0)
        
        
    def test_send_newsletter_several(self):
        
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello guys!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_blue.html',
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        
        sch_dt = timezone.now() - timedelta(1)
        sending = mommy.make(NewsletterSending, newsletter=newsletter, scheduling_dt= sch_dt, sending_dt= None)
        
        addresses = ';'.join(['toto@toto.fr']*5)
        management.call_command('send_newsletter', addresses, verbosity=0, interactive=False)
        
        sending = NewsletterSending.objects.get(id=sending.id)
        self.assertNotEqual(sending.sending_dt, None)
        
        self.assertEqual(len(mail.outbox), 5)
        for email in mail.outbox:
            self.assertEqual(email.to, ['toto@toto.fr'])
            self.assertEqual(email.subject, newsletter_data['subject'])
            self.assertTrue(email.body.find('Hello guys')>=0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find('Hello guys')>=0)
        
        #check whet happens if command is called again
        mail.outbox = []
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_newsletter_not_yet(self):
        
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello guys!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_blue.html',
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        
        sch_dt = timezone.now() + timedelta(1)
        sending = mommy.make(NewsletterSending, newsletter=newsletter, scheduling_dt= sch_dt, sending_dt= None)
        
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        
        sending = NewsletterSending.objects.get(id=sending.id)
        self.assertEqual(sending.sending_dt, None)
        
        self.assertEqual(len(mail.outbox), 0)
        
class AbsUrlTest(UserBaseTestCase):
    
    def setUp(self):
        super(AbsUrlTest, self).setUp()
        settings.SITE_ID = 1
        self.site = Site.objects.get(id=settings.SITE_ID)
        self.site.domain = "toto.fr"
        self.site.save()
        self.site_prefix = "http://"+self.site.domain
        self.newsletter = mommy.make(Newsletter, site=self.site)
        #settings.COOP_CMS_SITE_PREFIX = self.site_prefix
    
    def test_href(self):
        settings.COOP_CMS_SITE_PREFIX = self.site_prefix
        test_html = '<a href="%s/toto">This is a link</a>'
        rel_html = test_html % ""
        abs_html = BeautifulSoup(test_html % self.site_prefix).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html))
    
    def test_href(self):
        test_html = '<a href="%s/toto">This is a link</a>'
        rel_html = test_html % ""
        abs_html = BeautifulSoup(test_html % self.site_prefix).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html, self.newsletter))
        
    def test_src(self):
        test_html = '<h1>My image</h1><img src="%s/toto">'
        rel_html = test_html % ""
        abs_html = BeautifulSoup(test_html % self.site_prefix).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html, self.newsletter))
        
    def test_relative_path(self):
        test_html = '<h1>My image</h1><img src="%s/toto">'
        rel_html = test_html % "../../.."
        abs_html = BeautifulSoup(test_html % self.site_prefix).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html, self.newsletter))
    
    def test_src_and_img(self):
        test_html = '<h1>My image</h1><a href="{0}/a1">This is a link</a><img src="{0}/toto"/><img src="{0}/titi"/><a href="{0}/a2">This is another link</a>'
        rel_html = test_html.format("")
        html = test_html.format(self.site_prefix)
        abs_html = BeautifulSoup(html).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html, self.newsletter))
        
    def test_href_rel_and_abs(self):
        test_html = '<a href="%s/toto">This is a link</a><a href="http://www.apidev.fr">another</a>'
        rel_html = test_html % ""
        abs_html = BeautifulSoup(test_html % self.site_prefix).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html, self.newsletter))
        
    def test_style_in_between(self):
        test_html = u'<img style="margin: 0; width: 700px;" src="%s/media/img/newsletter_header.png" alt="Logo">'
        rel_html = test_html % ""
        abs_html = BeautifulSoup(test_html % self.site_prefix).prettify()
        self.assertEqual(abs_html, make_links_absolute(rel_html, self.newsletter))
        
    def test_missing_attr(self):
        test_html = u'<img alt="Logo" /><a name="aa">link</a>'
        abs_html = BeautifulSoup(test_html).prettify()
        self.assertEqual(abs_html, make_links_absolute(test_html, self.newsletter))
        
class NavigationTreeTest(BaseTestCase):
    
    def setUp(self):
        super(NavigationTreeTest, self).setUp()
        ct = ContentType.objects.get_for_model(get_article_class())
        nt_articles = NavType.objects.create(content_type=ct, search_field='title',
            label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        ct = ContentType.objects.get(app_label='coop_cms', model='link')
        nt_links = NavType.objects.create(content_type=ct, search_field='url',
            label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        self.default_tree = get_navtree_class().objects.create()
        self.tree1 = get_navtree_class().objects.create(name="tree1")
        self.tree2 = get_navtree_class().objects.create(name="tree2")
        self.tree2.types.add(nt_links)
        self.tree2.save()
        
    def test_view_default_navigation(self):
        tpl = Template('{% load coop_navigation %}{% navigation_as_nested_ul %}')
        
        link1 = Link.objects.create(url='http://www.google.fr', title="http://www.google.fr")
        link2 = Link.objects.create(url='http://www.apidev.fr', title="http://www.apidev.fr")
        art1 = get_article_class().objects.create(title='Article Number One', content='oups')
        art2 = get_article_class().objects.create(title='Article Number Two', content='hello')
        art3 = get_article_class().objects.create(title='Article Number Three', content='bye-bye')
        
        node1 = NavNode.objects.create(tree=self.default_tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        node2 = NavNode.objects.create(tree=self.default_tree, label=art1.title, content_object=art1, ordering=2, parent=None)
        node3 = NavNode.objects.create(tree=self.default_tree, label=art2.title, content_object=art2, ordering=1, parent=node2)
        node4 = NavNode.objects.create(tree=self.tree1, label=art3.title, content_object=art3, ordering=1, parent=None)
        node5 = NavNode.objects.create(tree=self.tree1, label=art1.title, content_object=art1, ordering=2, parent=None)
        node6 = NavNode.objects.create(tree=self.tree1, label=link2.url, content_object=link2, ordering=2, parent=node5)
        
        nodes_in, nodes_out = [art1, art2, link1], [art3, link2]
        
        html = tpl.render(Context({}))
        
        for n in nodes_in:
            self.assertTrue(html.find(unicode(n))>=0)
            
        for n in nodes_out:
            self.assertFalse(html.find(unicode(n))>=0)
            
    def test_view_alternative_navigation(self):
        tpl = Template('{% load coop_navigation %}{% navigation_as_nested_ul tree=tree1 %}')
        
        link1 = Link.objects.create(url='http://www.google.fr', title="http://www.google.fr")
        link2 = Link.objects.create(url='http://www.apidev.fr', title="http://www.apidev.fr")
        art1 = get_article_class().objects.create(title='Article Number One', content='oups')
        art2 = get_article_class().objects.create(title='Article Number Two', content='hello')
        art3 = get_article_class().objects.create(title='Article Number Three', content='bye-bye')
        
        node1 = NavNode.objects.create(tree=self.default_tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        node2 = NavNode.objects.create(tree=self.default_tree, label=art1.title, content_object=art1, ordering=2, parent=None)
        node3 = NavNode.objects.create(tree=self.default_tree, label=art2.title, content_object=art2, ordering=1, parent=node2)
        node4 = NavNode.objects.create(tree=self.tree1, label=art3.title, content_object=art3, ordering=1, parent=None)
        node5 = NavNode.objects.create(tree=self.tree1, label=art1.title, content_object=art1, ordering=2, parent=None)
        node6 = NavNode.objects.create(tree=self.tree1, label=link2.url, content_object=link2, ordering=2, parent=node5)
        
        nodes_in, nodes_out = [art1, art3, link2], [art2, link1]
        
        html = tpl.render(Context({}))
        
        for n in nodes_in:
            self.assertTrue(html.find(unicode(n))>=0)
            
        for n in nodes_out:
            self.assertFalse(html.find(unicode(n))>=0)
            
            
    def test_view_several_navigation(self):
        tpl = Template('{% load coop_navigation %}{% navigation_as_nested_ul tree=tree1 %}{% navigation_as_nested_ul tree=tree2 %}{% navigation_as_nested_ul %}')
        
        link1 = Link.objects.create(url='http://www.google.fr', title="http://www.google.fr")
        link2 = Link.objects.create(url='http://www.apidev.fr', title="http://www.apidev.fr")
        art1 = get_article_class().objects.create(title='Article Number One', content='oups')
        art2 = get_article_class().objects.create(title='Article Number Two', content='hello')
        art3 = get_article_class().objects.create(title='Article Number Three', content='bye-bye')
        
        node1 = NavNode.objects.create(tree=self.default_tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        node2 = NavNode.objects.create(tree=self.default_tree, label=art1.title, content_object=art1, ordering=2, parent=None)
        node3 = NavNode.objects.create(tree=self.default_tree, label=art2.title, content_object=art2, ordering=1, parent=node2)
        node4 = NavNode.objects.create(tree=self.tree1, label=art3.title, content_object=art3, ordering=1, parent=None)
        node5 = NavNode.objects.create(tree=self.tree1, label=art1.title, content_object=art1, ordering=2, parent=None)
        node6 = NavNode.objects.create(tree=self.tree2, label=link2.url, content_object=link2, ordering=2, parent=node5)
        
        nodes_in = [art1, art3, link2, art2, link1]
        
        html = tpl.render(Context({}))
        
        for n in nodes_in:
            self.assertTrue(html.find(unicode(n))>=0)
            
class HomepageTest(UserBaseTestCase):
    
    def setUp(self):
        super(HomepageTest, self).setUp()
        super(HomepageTest, self).setUp()
        self.site_id = settings.SITE_ID
    
    def tearDown(self):
        super(HomepageTest, self).tearDown()
        settings.SITE_ID = self.site_id
    
    def test_only_one_homepage(self):
        site = Site.objects.get(id=settings.SITE_ID)
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django', homepage_for_site=site)
        a3 = get_article_class().objects.create(title="home", content='homepage')
        
        self.assertEqual(1, get_article_class().objects.filter(homepage_for_site__id=settings.SITE_ID).count())
        self.assertEqual(a2.title, get_article_class().objects.filter(homepage_for_site__id=settings.SITE_ID)[0].title)
        
        a3.homepage_for_site = site
        a3.save()
        
        a2 = get_article_class().objects.get(id=a2.id)
        a3 = get_article_class().objects.get(id=a3.id)
        self.assertEqual(a3.is_homepage, True)
        self.assertEqual(a2.is_homepage, False)
        
        response = self.client.get(reverse('coop_cms_homepage'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].find(a3.get_absolute_url())>0)
        
    def test_only_one_homepage_again(self):
        site = Site.objects.get(id=settings.SITE_ID)
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django')
        a3 = get_article_class().objects.create(title="home", content='homepage')
        
        self.assertEqual(0, get_article_class().objects.filter(homepage_for_site__id=settings.SITE_ID).count())
        
        a3.homepage_for_site = site
        a3.save()
        
        a3 = get_article_class().objects.get(id=a3.id)
        self.assertEqual(a3.is_homepage, True)
        
        response = self.client.get(reverse('coop_cms_homepage'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].find(a3.get_absolute_url())>0)
    
    def test_view_change_homepage(self):
        self._log_as_editor()
        a1 = get_article_class().objects.create(title="python", content='python')
        
        response = self.client.get(reverse('coop_cms_set_homepage', args=[a1.id]))
        self.assertEqual(response.status_code, 200)
        
        a1 = get_article_class().objects.get(id=a1.id)
        self.assertEqual(a1.is_homepage, False)
    
    def test_change_homepage(self):
        self._log_as_editor()
        site = Site.objects.get(id=settings.SITE_ID)
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django')
        a3 = get_article_class().objects.create(title="home1", content='homepage1')
        
        response = self.client.post(reverse('coop_cms_set_homepage', args=[a2.id]), data={'confirm': '1'})
        self.assertEqual(response.status_code, 200)
        a2 = get_article_class().objects.get(id=a2.id)
        home_url = reverse("coop_cms_homepage")
        self.assertEqual(response.content,
            '<script>$.colorbox.close(); window.location="{0}";</script>'.format(home_url))
        self.assertEqual(a2.homepage_for_site.id, site.id)
        
        response = self.client.post(reverse('coop_cms_set_homepage', args=[a3.id]), data={'confirm': '1'})
        self.assertEqual(response.status_code, 200)
        home_url = reverse("coop_cms_homepage")
        self.assertEqual(response.content,
            '<script>$.colorbox.close(); window.location="{0}";</script>'.format(home_url))
        a2 = get_article_class().objects.get(id=a2.id)
        a3 = get_article_class().objects.get(id=a3.id)
        self.assertEqual(a2.homepage_for_site, None)
        self.assertEqual(a3.homepage_for_site.id, site.id)
    
    def test_change_homepage_anonymous(self):
        ite = Site.objects.get(id=settings.SITE_ID)
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django')
        a3 = get_article_class().objects.create(title="home1", content='homepage1')
        
        response = self.client.post(reverse('coop_cms_set_homepage', args=[a2.id]), data={'confirm': '1'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain[0][0], 302)
        self.assertTrue(response.redirect_chain[-1][0].find(reverse('django.contrib.auth.views.login'))>0)
        a2 = get_article_class().objects.get(id=a2.id)
        self.assertEqual(a2.homepage_for_site, None)
        
        
    def test_change_homepage_multisites(self):
        self._log_as_editor()
        site1 = Site.objects.get(id=settings.SITE_ID)
        site2 = Site.objects.create(domain="wooooooaa.com", name="wooaa")
        
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django')
        a3 = get_article_class().objects.create(title="home1", content='homepage1')
        
        settings.SITE_ID = site2.id
        a4 = get_article_class().objects.create(title="home1", content='homepage2')
        
        settings.SITE_ID = site1.id
        response = self.client.post(reverse('coop_cms_set_homepage', args=[a3.id]), data={'confirm': '1'})
        home_url = reverse("coop_cms_homepage")
        self.assertEqual(response.content,
            '<script>$.colorbox.close(); window.location="{0}";</script>'.format(home_url))
        a3 = get_article_class().objects.get(id=a3.id)
        self.assertEqual(a3.homepage_for_site.id, site1.id)
        
        settings.SITE_ID = site2.id
        response = self.client.post(reverse('coop_cms_set_homepage', args=[a4.id]), data={'confirm': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,
            '<script>$.colorbox.close(); window.location="{0}";</script>'.format(home_url))
        a4 = get_article_class().objects.get(id=a4.id)
        a3 = get_article_class().objects.get(id=a3.id)
        self.assertEqual(a4.homepage_for_site.id, site2.id)
        self.assertEqual(a3.homepage_for_site.id, site1.id)
        
        
    def test_homepage_multisites(self):
        site1 = Site.objects.get(id=settings.SITE_ID)
        site2 = Site.objects.create(domain="wooooooaa.com", name="wooaa")
        
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django')
        a3 = get_article_class().objects.create(title="home1", content='homepage1')
        a4 = get_article_class().objects.create(title="home2", content='homepage2')
        
        self.assertEqual(0, get_article_class().objects.filter(homepage_for_site__id=settings.SITE_ID).count())
        
        a3.homepage_for_site = site1
        a3.save()
        
        a4.homepage_for_site = site2
        a4.save()
        
        home1 = get_article_class().objects.get(homepage_for_site__id=site1.id)
        home2 = get_article_class().objects.get(homepage_for_site__id=site2.id)
        
        self.assertEqual(a3.id, home1.id)
        self.assertEqual(a4.id, home2.id)
        
        settings.SITE_ID = site1.id
        response = self.client.get(reverse('coop_cms_homepage'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].find(home1.get_absolute_url()))
        self.assertEqual(home1.is_homepage, True)
        self.assertEqual(home2.is_homepage, False)
        
        settings.SITE_ID = site2.id
        response = self.client.get(reverse('coop_cms_homepage'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].find(home2.get_absolute_url()))
        self.assertEqual(home1.is_homepage, False)
        self.assertEqual(home2.is_homepage, True)
        
        
        
class UrlLocalizationTest(BaseTestCase):
    
    def setUp(self):
        activate(settings.LANGUAGES[0][0])
    
    def tearDown(self):
        activate(settings.LANGUAGES[0][0])
    
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
    
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_get_locale_article(self):
        original_text = '*!-+' * 10
        translated_text = ':%@/' * 9
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        setattr(a1, 'title_'+trans_lang, 'Accueil')
        setattr(a1, 'content_'+trans_lang, translated_text)
        a1.save()
        
        response = self.client.get('/{0}/home/'.format(origin_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        response = self.client.get('/{0}/accueil/'.format(trans_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, translated_text)

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_change_lang(self):
        
        original_text = '*!-+' * 10
        translated_text = ':%@/' * 9
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        setattr(a1, 'title_'+trans_lang, 'Accueil')
        setattr(a1, 'content_'+trans_lang, translated_text)
        
        a1.save()
        
        origin_url = '/{0}/home'.format(origin_lang)
        response = self.client.get(origin_url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        data = {'language': trans_lang}
        response = self.client.post(reverse('coop_cms_change_language')+'?next={0}'.format(origin_url),
            data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, translated_text)
        
        response = self.client.get('/{0}/accueil/'.format(trans_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, translated_text)
            
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_change_lang_no_trans(self):
        
        original_text = '*!-+' * 10
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        origin_url = '/{0}/home'.format(origin_lang)
        response = self.client.get(origin_url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        data = {'language': trans_lang}
        response = self.client.post(reverse('coop_cms_change_language')+'?next={0}'.format(origin_url),
            data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        response = self.client.get('/{0}/home/'.format(trans_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
            
    def test_keep_slug(self):
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        original_slug = a1.slug
        a1.title = "Title changed"
        a1.save()
        a1 = Article.objects.get(id=a1.id)
        self.assertEqual(original_slug, a1.slug)
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_keep_localized_slug(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, u'Accueil')
        a1.save()
        
        original_slug = a1.slug
        original_trans_slug = getattr(a1, 'slug_'+trans_lang, u'**dummy**')
        
        a1.title = u"Title changed"
        setattr(a1, 'title_'+trans_lang, u'Titre change')
        
        a1.save()
        a1 = Article.objects.get(id=a1.id)
        
        self.assertEqual(original_slug, a1.slug)
        self.assertEqual(original_trans_slug, getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa")

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, a2.title)
        a1.save()
        
        a2.save()
        
        setattr(a2, 'title_'+trans_lang, a2.title)
        a2.save()
        
        self.assertNotEqual(getattr(a2, 'slug_'+trans_lang), getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing2(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa")

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, a2.title)
        a1.save()
        
        setattr(a2, 'title_'+trans_lang, a2.title)
        a2.save()
        
        self.assertNotEqual(getattr(a2, 'slug_'+trans_lang), getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing3(self):
        self._log_as_editor()
        Article = get_article_class()

        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, a2.title)
        a1.save()
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a2.get_edit_url()
        
        data = {
            'title': a2.title,
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a2_updated = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a2_updated, 'title_'+trans_lang), a2.title)
        
        self.assertNotEqual(getattr(a2_updated, 'slug_'+trans_lang), getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localize_existing_article1(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a1.get_edit_url()
        
        data = {
            'title': u"Home",
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a1_updated = Article.objects.get(id=a1.id)
        
        self.assertEqual(getattr(a1_updated, 'title_'+trans_lang), a1.title)
        self.assertEqual(getattr(a1_updated, 'slug_'+trans_lang), getattr(a1, 'slug_'+origin_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localize_existing_article2(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Accueil", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a1.get_edit_url()
        
        data = {
            'title': u"Home",
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a1_updated = Article.objects.get(id=a1.id)
        self.assertEqual(getattr(a1_updated, 'title_'+origin_lang), a1.title)
        self.assertEqual(getattr(a1_updated, 'title_'+trans_lang), data["title"])
        self.assertEqual(getattr(a1_updated, 'slug_'+trans_lang), "home")
        self.assertEqual(getattr(a1_updated, 'slug_'+origin_lang), "accueil")
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing4(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        self.assertEqual(None, getattr(a2, 'slug_'+trans_lang))
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a2.get_edit_url()
        
        data = {
            'title': a1.title,
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a2_updated = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a2_updated, 'title_'+trans_lang), a1.title)
        
        self.assertNotEqual(getattr(a2_updated, 'slug_'+trans_lang), a1.slug)
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing5(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        self.assertEqual(None, getattr(a2, 'slug_'+trans_lang))
        
        setattr(a2, 'title_'+trans_lang, a1.title)
        a2.save()
        self.assertNotEqual(a1.slug, getattr(a2, 'slug_'+trans_lang))
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a2.get_edit_url()
        
        data = {
            'title': a1.title,
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a2_updated = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a2_updated, 'title_'+trans_lang), a1.title)
        
        self.assertNotEqual(getattr(a2_updated, 'slug_'+trans_lang), a1.slug)
            
    def test_no_title(self):
        Article = get_article_class()
        
        try:
            a1 = Article.objects.create(title=u"", content="a!*%:"*10, publication=BaseArticle.PUBLISHED)
        except:
            return #OK
        
        self.assertFalse(True) #Force to fail
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_create_article_in_additional_lang(self):
        
        Article = get_article_class()
        
        default_lang = settings.LANGUAGES[0][0]
        other_lang = settings.LANGUAGES[1][0]
        
        activate(other_lang)
        
        a1 = Article.objects.create(title=u"abcd", content="a!*%:"*10, publication=BaseArticle.PUBLISHED)
        
        response = self.client.get(a1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, a1.content)
        
        activate(default_lang)
        
        response = self.client.get(a1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, a1.content)

class PieceOfHtmlTagsTest(BaseTestCase):
    
    def test_create_poc(self):
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({}))
        self.assertEqual(html, "")
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_existing_poc(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_create_poc_read_only(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" read-only %}')
        html = tpl.render(Context({}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_create_edit_poc(self):
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertNotEqual(html, "")
        
        soup = BeautifulSoup(html)
        tags = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].text, "")
        
        tags_hidden = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content_hidden")
        self.assertEqual(len(tags_hidden), 1)
        self.assertEqual(tags_hidden[0].get("value", ""), "")
        
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_edit_poc(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertNotEqual(html, poc.content)
        
        soup = BeautifulSoup(html)
        tags = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].text, poc.content)
        
        tags_hidden = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content_hidden")
        self.assertEqual(len(tags_hidden), 1)
        self.assertEqual(tags_hidden[0]["value"], poc.content)
        
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_edit_poc_read_only(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" read-only %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
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


class AliasTest(BaseTestCase):
    
    def test_redirect(self):
        Article = get_article_class()
        article = Article.objects.create(slug="test", title="TestAlias", content="TestAlias")
        alias = Alias.objects.create(path='toto', redirect_url=article.get_absolute_url())
        
        response = self.client.get(alias.get_absolute_url())
        self.assertEqual(response.status_code, 301)
        
        response = self.client.get(alias.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, article.title)
        
        
    def test_redirect_no_url(self):
        alias = Alias.objects.create(path='toto', redirect_url='')
        response = self.client.get(alias.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        
    def test_redirect_no_alias(self):
        response = self.client.get(reverse('coop_cms_view_article', args=['toto']))
        self.assertEqual(response.status_code, 404)
        
class MultiSiteTest(BaseTestCase):
    
    def tearDown(self):
        super(MultiSiteTest, self).tearDown()
        site1 = Site.objects.all()[0]
        settings.SITE_ID = site1.id
    
    def test_view_article(self):
        site1 = Site.objects.all()[0]
        site2 = Site.objects.create(domain='hhtp://test2', name="Test2")
        settings.SITE_ID = site1.id
        
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)

    def test_view_article_on_site2(self):
        site1 = Site.objects.all()[0]
        site2 = Site.objects.create(domain='hhtp://test2', name="Test2")
        settings.SITE_ID = site2.id
        
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_view_article_on_all_sites(self):
        site1 = Site.objects.all()[0]
        site2 = Site.objects.create(domain='hhtp://test2', name="Test2")
        settings.SITE_ID = site1.id
        
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        article.sites.add(site2)
        article.save()
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
        settings.SITE_ID = site2.id
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)


    def test_view_404_site2(self):
        site1 = Site.objects.all()[0]
        site2 = Site.objects.create(domain='hhtp://test2', name="Test2")
        settings.SITE_ID = site1.id
        
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        
        settings.SITE_ID = site2.id
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
    def test_view_only_site2(self):
        site1 = Site.objects.all()[0]
        site2 = Site.objects.create(domain='hhtp://test2', name="Test2")
        settings.SITE_ID = site1.id
        
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        article.sites.remove(site1)
        article.sites.add(site2)
        article.save()
        
        settings.SITE_ID = site1.id
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
        settings.SITE_ID = site2.id
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        

class NewsletterFriendlyTemplateTagsTest(BaseTestCase):
    
    template_content = """
        {{% load coop_utils %}}
        {{% nlf_css {0} %}}
            <a>One</a>
            <a>Two</a>
            <a>Three</a>
            <img />
            <table><tr><td></td><td></td></table>
            <table class="this-one"><tr><td></td><td></td></table>
        {{% end_nlf_css %}}
    """
    
    def test_email_mode_is_inline(self):
        template = self.template_content.format('a="color: red;"')
        tpl = Template(template)
        html = tpl.render(Context({'by_email': True}))
        self.assertEqual(0, html.count(u'<style>'))
        self.assertEqual(3, html.count(u'<a style="color: red;">'))
        
    def test_edit_mode_is_in_style(self):
        template = self.template_content.format('a="color: red;"')
        tpl = Template(template)
        html = tpl.render(Context({'by_email': False}))
        self.assertEqual(1, html.count(u'<style>'))
        self.assertEqual(1, html.count(u'a { color: red; }'))
        self.assertEqual(0, html.count(u'<a style="color: red;">'))
        
    def test_several_args_email_mode_is_inline(self):
        template = self.template_content.format('a="color: red; background: blue;" td="border: none;" img="width: 100px;"')
        tpl = Template(template)
        html = tpl.render(Context({'by_email': True}))
        self.assertEqual(0, html.count(u'<style>'))
        self.assertEqual(3, html.count(u'<a style="color: red; background: blue;">'))
        self.assertEqual(1, html.count(u'<img style="width: 100px;"/>'))
        self.assertEqual(4, html.count(u'<td style="border: none;">'))
        
    def test_several_args_edit_mode_is_in_style(self):
        template = self.template_content.format('a="color: red; background: blue;" td="border: none;" img="width: 100px;"')
        tpl = Template(template)
        html = tpl.render(Context({'by_email': False}))
        self.assertEqual(1, html.count(u'<style>'))
        self.assertEqual(1, html.count(u'a { color: red; background: blue; }'))
        self.assertEqual(1, html.count(u'img { width: 100px; }'))
        self.assertEqual(1, html.count(u'td { border: none; }'))
        self.assertEqual(0, html.count(u'<a style="color: red; background: blue;">'))
        self.assertEqual(0, html.count(u'<img style="width: 100px;">'))
        self.assertEqual(0, html.count(u'<td style="border: none;">'))
        
    def test_class_selector_email_mode_is_inline(self):
        template = self.template_content.format('"table.this-one td"="border: none;"')
        tpl = Template(template)
        html = tpl.render(Context({'by_email': True}))
        self.assertEqual(0, html.count(u'<style>'))
        self.assertEqual(0, html.count(u'<a style="color: red; background: blue;">'))
        self.assertEqual(0, html.count(u'<img style="width: 100px;"/>'))
        self.assertEqual(2, html.count(u'<td style="border: none;">'))

class GenericViewTestCase(BaseGenericViewTestCase):
    warning = """
    Add this to your settings.py to enable this test:
    if len(sys.argv)>1 and 'test' == sys.argv[1]:
        INSTALLED_APPS = INSTALLED_APPS + ('coop_cms.apps.test_app',)
    """
    
    def setUp(self):
        super(GenericViewTestCase, self).setUp()
        if not ('coop_cms.apps.test_app' in settings.INSTALLED_APPS):
            print self.warning
            raise SkipTest()


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
        
class FragmentsTest(BaseTestCase):
    
    editable_field_tpl = '<div class="djaloha-editable" id="djaloha_djaloha__coop_cms__Fragment__id__{0}__content">' + \
        '{1}</div>\n<input type="hidden" id="djaloha_djaloha__coop_cms__Fragment__id__{0}__content_hidden" ' + \
        'name="djaloha__coop_cms__Fragment__id__{0}__content" value="{1}">'
    
    def setUp(self):
        super(FragmentsTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article_with_fragments.html', 'Article with fragments'),
            ('test/article_with_fragments_extra_id.html', 'Article with fragments extra id'),
        )
        
    def tearDown(self):
        super(FragmentsTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates

    def test_fragment_position(self):
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        
        f1 = mommy.make(Fragment, type=ft1)
        f2 = mommy.make(Fragment, type=ft1)
        f3 = mommy.make(Fragment, type=ft1)
        f4 = mommy.make(Fragment, type=ft1)
        
        g1 = mommy.make(Fragment, type=ft2)
        g2 = mommy.make(Fragment, type=ft2)
        g3 = mommy.make(Fragment, type=ft2)
        
        f5 = mommy.make(Fragment, type=ft1)
        
        for idx, elt in enumerate([f1, f2, f3, f4, f5]):
            self.assertEqual(idx+1, elt.position)
        
        for idx, elt in enumerate([g1, g2, g3]):
            self.assertEqual(idx+1, elt.position)
            
    def test_fragment_position_extra_id(self):
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        ff1 = mommy.make(FragmentFilter)
        ff2 = mommy.make(FragmentFilter)
        
        f1 = mommy.make(Fragment, type=ft1, filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, filter=ff1)
        
        f4 = mommy.make(Fragment, type=ft1, filter=ff2)
        
        g1 = mommy.make(Fragment, type=ft2, filter=ff1)
        g2 = mommy.make(Fragment, type=ft2, filter=ff2)
        g3 = mommy.make(Fragment, type=ft2, filter=ff2)
        
        f5 = mommy.make(Fragment, type=ft1, filter=ff1)
        
        f6 = mommy.make(Fragment, type=ft1)
        f7 = mommy.make(Fragment, type=ft1)
        
        for idx, elt in enumerate([f1, f2, f3, f5]):
            self.assertEqual(idx+1, elt.position)
            
        for idx, elt in enumerate([f4]):
            self.assertEqual(idx+1, elt.position)
        
        for idx, elt in enumerate([g1]):
            self.assertEqual(idx+1, elt.position)
            
        for idx, elt in enumerate([g2, g3]):
            self.assertEqual(idx+1, elt.position)
            
        for idx, elt in enumerate([f6, f7]):
            self.assertEqual(idx+1, elt.position)
            
    def test_fragment_position_update(self):
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        
        f1 = mommy.make(Fragment, type=ft1)
        f2 = mommy.make(Fragment, type=ft1)
        f3 = mommy.make(Fragment, type=ft1)
        
        f1.save()
        f2.save()
        f3.save()
        
        for idx, elt in enumerate([f1, f2, f3]):
            self.assertEqual(idx+1, elt.position)
            
    def test_view_fragments(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2, f3]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def test_view_fragments_extra_id(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ff1 = mommy.make(FragmentFilter, extra_id="1")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name x %}')
        html = tpl.render(Context({"ft_name": ft_name, "x": 1}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        soup = BeautifulSoup(html)
        ft_tags = soup.select(".coop-fragment-type")
        self.assertEqual(len(ft_tags), 1)
        ft_tag = ft_tags[0]
        self.assertEqual(ft_tag['rel'], str(ft1.id))
        self.assertEqual(ft_tag['data-filter'], str(ff1.id))
        
        
        for f in [f3, f4]:
            self.assertTrue(html.find(f.content)<0)
        
    def test_fragments_with_extra_id(self):
        ft_name = u"contacts"
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name x %}')
        html = tpl.render(Context({"ft_name": ft_name, 'x': 2}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)

        self.assertEqual(FragmentFilter.objects.count(), 1)
        self.assertEqual(FragmentFilter.objects.filter(extra_id='2').count(), 1)
        
    def test_view_fragments_name_as_string(self):
        ft1 = mommy.make(FragmentType, name="contacts")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments "contacts" %}')
        html = tpl.render(Context({"ft_name": "contacts"}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2, f3]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def test_view_fragments_name_and_extra_id_as_string(self):
        ft1 = mommy.make(FragmentType, name="contacts")
        ff1 = mommy.make(FragmentFilter, extra_id="hello")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments "contacts" "hello" %}')
        html = tpl.render(Context({"ft_name": "contacts"}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        for f in [f3, f4]:
            self.assertTrue(html.find(f.content)<0)
        
    def test_view_fragments_order(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", position=3)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", position=1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", position=2)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f2, f3, f1]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def test_view_only_specified_fragments(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f2, f3, f1]]
        for pos in positions:
            self.assertTrue(pos>=0)
        
        positions = [html.find('{0}'.format(f.content)) for f in [g1]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_view_only_specified_fragments_extra_id(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        ff1 = mommy.make(FragmentFilter, extra_id="hello")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT", filter=ff1)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name "hello" %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f2, f1]]
        for pos in positions:
            self.assertTrue(pos>=0)
        
        positions = [html.find('{0}'.format(f.content)) for f in [g1, f3, f4]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_view_fragments_edit_mode(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name, "form": True}))
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [f1, f2, f3]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [g1]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_view_fragments_extra_id_edit_mode(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        ff1 = mommy.make(FragmentFilter, extra_id="hello")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name "hello" %}')
        html = tpl.render(Context({"ft_name": ft_name, "form": True}))
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [f1, f2]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [g1, f3, f4]]
        for pos in positions:
            self.assertTrue(pos==-1)
    
    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct1 = ContentType.objects.get_for_model(get_article_class())
        ct2 = ContentType.objects.get_for_model(Fragment)
        
        for ct in (ct1, ct2):
            
            perm = 'change_{0}'.format(ct.model)
            can_edit = Permission.objects.get(content_type=ct, codename=perm)
            user.user_permissions.add(can_edit)
            
            perm = 'add_{0}'.format(ct.model)
            can_add = Permission.objects.get(content_type=ct, codename=perm)
            user.user_permissions.add(can_add)
        
        user.is_active = True
        user.save()
        return self.client.login(username='toto', password='toto')
    
    def _log_as_regular_user(self):
        user = User.objects.create_user('titi', 'titi@toto.fr', 'titi')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        user.is_active = True
        user.save()
        return self.client.login(username='titi', password='titi')
        
    
    def _check_article(self, response, data):
        for (key, value) in data.items():
            self.assertContains(response, value)
    #        
    #def _check_article_not_changed(self, article, data, initial_data):
    #    article = get_article_class().objects.get(id=article.id)
    #
    #    for (key, value) in data.items():
    #        self.assertNotEquals(getattr(article, key), value)
    #        
    #    for (key, value) in initial_data.items():
    #        self.assertEquals(getattr(article, key), value)

    def test_view_article_no_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FragmentType.objects.count())
        self.assertEqual("parts", FragmentType.objects.all()[0].name)
        
    def test_view_article_with_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop")
        
        response = self.client.get(article.get_absolute_url())
        
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.content)
        
    def test_view_article_with_fragments_extra_id(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[1][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        ff1 = mommy.make(FragmentFilter, extra_id=str(article.id))
        ff2 = mommy.make(FragmentFilter, extra_id="hello")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop", filter=ff1)
        f2 = mommy.make(Fragment, type=ft, content="QSDFGHJKLM", filter=ff2)
        f3 = mommy.make(Fragment, type=ft, content="Wxcvbn,;:=", filter=None)
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.content)
        self.assertNotContains(response, f2.content)
        self.assertNotContains(response, f3.content)
        
    def test_view_article_with_fragment_with_css(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop", css_class="this-is-my-fragment")
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.content)
        
        soup = BeautifulSoup(response.content)
        fragment = soup.select("div."+f1.css_class)[0]
        self.assertEqual(f1.content, fragment.text)
        
    def test_edit_article_no_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        data = {"title": 'salut', 'content': 'bonjour!'}
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
        data = {"title": 'bye', 'content': 'au revoir'}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
    def test_edit_article_with_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop")
        
        new_f1_content = u"Qsdfghjklm"
        data = {
            "title": 'salut',
            'content': 'bonjour!',
            'djaloha__coop_cms__Fragment__id__{0}__content'.format(f1.id): new_f1_content,
        }
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, data['title'])
        self.assertContains(response, data['content'])
        self.assertContains(response, new_f1_content)
        
    def test_edit_article_with_fragments_extra_id(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[1][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        ff = mommy.make(FragmentFilter, extra_id=str(article.id))
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop", filter=ff)
        
        new_f1_content = u"Qsdfghjklm"
        data = {
            "title": 'salut',
            'content': 'bonjour!',
            'djaloha__coop_cms__Fragment__id__{0}__content'.format(f1.id): new_f1_content,
        }
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, data['title'])
        self.assertContains(response, data['content'])
        self.assertContains(response, new_f1_content)
        
    def test_view_add_fragment(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
    def test_view_add_fragment_check_filters(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[1][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        #url = reverse("coop_cms_add_fragment")
        url = article.get_edit_url()
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        ft_tags = soup.select(".coop-fragment-type")
        ft_objs = FragmentType.objects.all()
        ff_objs = FragmentFilter.objects.all()
        
        self.assertEqual(len(ft_tags), 2)
        self.assertEqual(ft_objs.count(), 2)
        self.assertEqual(ff_objs.count(), 1)
        
        for i in range(2):
            self.assertEqual(int(ft_tags[i]["rel"]), ft_objs[i].id)
        
        self.assertEqual(ft_tags[0]["data-filter"], '')
        self.assertEqual(ft_tags[1]["data-filter"], str(ff_objs[0].id))
        
        
    def test_view_add_fragment_no_filter_check_filters(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        #url = reverse("coop_cms_add_fragment")
        url = article.get_edit_url()
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        ft_tags = soup.select(".coop-fragment-type")
        ft_objs = FragmentType.objects.all()
        ff_objs = FragmentFilter.objects.all()
        
        self.assertEqual(len(ft_tags), 1)
        self.assertEqual(ft_objs.count(), 1)
        self.assertEqual(ff_objs.count(), 0)
        
        self.assertEqual(int(ft_tags[0]["rel"]), ft_objs[0].id)
        
        self.assertEqual(ft_tags[0]["data-filter"], '')
        
    def test_view_add_fragment_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        
        self._log_as_regular_user()
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)
        
    def _add_fragment(self, data, errors_count=0):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        if errors_count:
            self.assertEqual(errors_count, len(errs))
        else:
            self.assertEqual([], errs)
            expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
            self.assertEqual(response.content, expected)
        
        return response        
        
    def test_add_fragment(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 0,
            'filter': '',
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')   
        self.assertEqual(f.position, 1)
        self.assertEqual(f.filter, None)

        
    def test_add_fragment_filter(self):
        ft = mommy.make(FragmentType, name="parts")
        ff = mommy.make(FragmentFilter, extra_id="2")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 0,
            'filter': ff.id
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')   
        self.assertEqual(f.position, 1)
        self.assertEqual(f.filter, ff)
        
    def test_add_fragment_position(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 2,
            'filter': '',
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')
        self.assertEqual(f.position, 2)
        
    def test_add_fragment_invalid_filter(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 2,
            'filter': '0',
        }
        
        response = self._add_fragment(data, 1)
        self.assertEqual(0, Fragment.objects.count())
        
    def test_add_fragment_css(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'css_class': 'okidki',
            'position': 0,
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')   
        self.assertEqual(f.position, 1)
            
    def test_view_add_fragment_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft,
            'name': 'abcd',
            'css_class': 'okidoki',
            'position': 0,
        }
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.post(url, data=data, follow=False)
        self.assertEqual(302, response.status_code)
        next_url = "http://testserver/accounts/login/?next={0}".format(url)
        self.assertEqual(next_url, response['Location'])
        
        self._log_as_regular_user()
        response = self.client.post(url, data=data, follow=False)
        self.assertEqual(403, response.status_code)
        
        self.assertEqual(0, Fragment.objects.count())
        
    def test_view_edit_fragments_empty(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
    def test_view_edit_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        f1 = mommy.make(Fragment, name="azerty")
        f2 = mommy.make(Fragment, name="qwerty")
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.name)
        self.assertContains(response, f2.name)
        
    def test_view_edit_fragments_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.get(url)
        
        self.assertEqual(302, response.status_code)
        
        self._log_as_regular_user()
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)    
    
    def test_edit_fragment(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 5)
    
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty+")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 2)

    def test_edit_fragment_css_allowed(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType, allowed_css_classes="oups")
        ft2 = mommy.make(FragmentType, allowed_css_classes="aaa,bbb")
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "oups")   
        self.assertEqual(f1.position, 5)
    
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty+")
        self.assertEqual(f2.css_class, "aaa")   
        self.assertEqual(f2.position, 2)
  
    def test_edit_fragment_css_not_allowed(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType, allowed_css_classes="")
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 5)
    
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty+")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 2)
  
      
    def test_edit_fragment_delete(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "",
            'form-1-position': 2,
            'form-1-delete_me': True,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(1, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        self.assertEqual(Fragment.objects.filter(id=f2.id).count(), 0)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 5)
        
    def test_edit_fragment_invalid_position(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': "AAA",
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual(1, len(errs))
    
    def test_edit_fragment_empty_name(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': "",
            'form-0-css_class': "oups",
            'form-0-position': 1,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual(1, len(errs))
        
    
    def test_edit_fragment_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=False)
        
        self.assertEqual(302, response.status_code)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 1)
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 1)

        self._log_as_regular_user()
        response = self.client.post(url, data=data)
        self.assertEqual(403, response.status_code)  
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 1)
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 1)
        
class ArticlesByCategoryTest(BaseTestCase):

    def test_view_articles(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory)
        art = mommy.make(Article, category=cat, title=u"AZERTYUIOP", publication=BaseArticle.PUBLISHED)
        
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, art.title)
    
    def test_view_articles_ordering(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory)
        
        dt1 = datetime.now() + timedelta(1)
        dt2 = datetime.now()
        dt3 = datetime.now() - timedelta(2)
        dt4 = datetime.now() - timedelta(1)
        
        
        art1 = mommy.make(Article, category=cat, title=u"#ITEM1#", publication_date=dt1,
            publication=BaseArticle.PUBLISHED)
        art2 = mommy.make(Article, category=cat, title=u"#ITEM2#", publication_date=dt2,
            publication=BaseArticle.PUBLISHED)
        art3 = mommy.make(Article, category=cat, title=u"#ITEM3#", publication_date=dt3,
            publication=BaseArticle.PUBLISHED)
        art4 = mommy.make(Article, category=cat, title=u"#ITEM4#", publication_date=dt4,
            publication=BaseArticle.PUBLISHED)
        
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertContains(response, art3.title)
        self.assertContains(response, art4.title)
        
        content = response.content.decode('utf-8')
        articles = sorted((art1, art2, art3, art4), key=lambda x: x.publication_date)
        articles.reverse()
        
        positions = [content.find(a.title) for a in articles]
        
        self.assertEqual(positions, sorted(positions))
        
        
    def test_view_no_articles(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory)
        
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_view_no_published_articles(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory)
        art = mommy.make(Article, category=cat, title=u"AZERTYUIOP", publication=BaseArticle.DRAFT)
        
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_view_articles_publication(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory)
        art1 = mommy.make(Article, category=cat, title=u"AZERTYUIOP", publication=BaseArticle.PUBLISHED)
        art2 = mommy.make(Article, category=cat, title=u"QSDFGHJKLM", publication=BaseArticle.DRAFT)
        
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, art1.title)
        self.assertNotContains(response, art2.title)
        
    def test_view_articles_different_categories(self):
        Article = get_article_class()
        cat1 = mommy.make(ArticleCategory)
        cat2 = mommy.make(ArticleCategory)
        art1 = mommy.make(Article, category=cat1, title=u"AZERTYUIOP", publication=BaseArticle.PUBLISHED)
        art2 = mommy.make(Article, category=cat2, title=u"QSDFGHJKLM", publication=BaseArticle.PUBLISHED)
        
        url = reverse('coop_cms_articles_category', args=[cat1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, art1.title)
        self.assertNotContains(response, art2.title)
        
        
    def test_view_articles_unknwonw_categories(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory, name="abcd")
        art = mommy.make(Article, category=cat, title=u"AZERTYUIOP", publication=BaseArticle.PUBLISHED)
        
        url = reverse('coop_cms_articles_category', args=["ghjk"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_view_articles_category_template(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory, name="Only for unit testing")
        art = mommy.make(Article, category=cat, title=u"AZERTYUIOP", publication=BaseArticle.PUBLISHED)
        self.assertEqual(cat.slug, "only-for-unit-testing")
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, art.title)
        self.assertContains(response, "This comes from custom template")
        
    def test_view_articles_category_many(self):
        Article = get_article_class()
        cat = mommy.make(ArticleCategory)
        for i in range(30):
            art = mommy.make(Article, category=cat, publication_date=datetime(2014, 3, i+1),
                title=u"AZERTY-{0}-UIOP".format(i), publication=BaseArticle.PUBLISHED)
        
        url = reverse('coop_cms_articles_category', args=[cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        ids = list(range(30))
        ids.reverse()
        for i in ids[:10]:
            self.assertContains(response, u"AZERTY-{0}-UIOP".format(i))
        for i in ids[10:]:
            self.assertNotContains(response, u"AZERTY-{0}-UIOP".format(i))
            
        response = self.client.get(url+"?page=2")
        self.assertEqual(response.status_code, 200)
        for i in ids[10:20]:
            self.assertContains(response, u"AZERTY-{0}-UIOP".format(i))
        for i in ids[:10]:
            self.assertNotContains(response, u"AZERTY-{0}-UIOP".format(i))
        
        
class CoopCategoryTemplateTagTest(BaseTestCase):
    
    def test_use_template(self):
        tpl = Template('{% load coop_utils %}{% coop_category "abc" def %}!!{{def}}!!')
        html = tpl.render(Context({}))
        self.assertEqual(ArticleCategory.objects.count(), 1)
        self.assertEqual(html, "!!abc!!")
        
    def test_use_template_several_times(self):
        tpl = Template('{% load coop_utils %}{% coop_category "joe" bar %}{% coop_category "abc" def %}!!{{def}}-{{bar}}!!')
        html = tpl.render(Context({}))
        self.assertEqual(ArticleCategory.objects.count(), 2)
        self.assertEqual(html, "!!abc-joe!!")
        
    def test_use_template_many_calls(self):
        tpl = Template('{% load coop_utils %}{% coop_category "abc" def %}!!{{def}}!!')
        for i in range(10):
            html = tpl.render(Context({}))
        self.assertEqual(ArticleCategory.objects.count(), 1)
        self.assertEqual(html, "!!abc!!")
    
    def test_use_template_many_calls_not_slug(self):
        tpl = Template('{% load coop_utils %}{% coop_category "Ab CD" def %}!!{{def}}!!')
        for i in range(10):
            html = tpl.render(Context({}))
        self.assertEqual(ArticleCategory.objects.count(), 1)
        self.assertEqual(html, "!!Ab CD!!")
        
    def test_use_template_existing_category(self):
        mommy.make(ArticleCategory, name="abc")
        tpl = Template('{% load coop_utils %}{% coop_category "abc" def %}!!{{def}}!!')
        html = tpl.render(Context({}))
        self.assertEqual(ArticleCategory.objects.count(), 1)
        self.assertEqual(html, "!!abc!!")
        
    def test_use_template_as_variable(self):
        mommy.make(ArticleCategory, name="abc")
        tpl = Template('{% load coop_utils %}{% coop_category cat def %}!!{{def}}!!')
        html = tpl.render(Context({'cat': u"abc"}))
        self.assertEqual(ArticleCategory.objects.count(), 1)
        self.assertEqual(html, "!!abc!!")
        
    def test_view_category_articles(self):
        cat = mommy.make(ArticleCategory, name="abc")
        art1 = mommy.make(get_article_class(), category=cat, publication=True, publication_date=datetime.now())
        art2 = mommy.make(get_article_class(), category=cat, publication=True,
            publication_date=datetime.now()-timedelta(1))
        
        self.assertEqual(list(cat.get_articles_qs().all()), [art2, art1])
        

    def test_view_category_articles_not_all_published(self):
        cat = mommy.make(ArticleCategory, name="abc")
        art1 = mommy.make(get_article_class(), category=cat, publication=False)
        art2 = mommy.make(get_article_class(), category=cat, publication=True)
        
        
        self.assertEqual(list(cat.get_articles_qs().all()), [art2])

class ArticleLogoTest(BaseArticleTest):
    
    def _get_file(self, file_name='unittest1.png'):
        full_name = os.path.normpath(os.path.dirname(__file__) + '/fixtures/' + file_name)
        return open(full_name, 'rb')
    
    def setUp(self):
        super(ArticleLogoTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article_with_logo_size.html', 'Article with logo size'),
            ('test/article_with_logo_size_and_crop.html', 'Article with logo size and crop'),
            ('test/article_no_logo_size.html', 'Article no logo size and crop'),
        )
        self._default_logo_size = getattr(settings, 'COOP_CMS_ARTICLE_LOGO_SIZE', None)
        self._default_logo_crop = getattr(settings, 'COOP_CMS_ARTICLE_LOGO_CROP', None)
        
    def tearDown(self):
        super(ArticleLogoTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates
        settings.COOP_CMS_ARTICLE_LOGO_SIZE = self._default_logo_size
        settings.COOP_CMS_ARTICLE_LOGO_CROP = self._default_logo_crop
        
    def test_view_article_no_image(self, template_index=0, image=False):
        Article = get_article_class()
        a = mommy.make(Article,
            title=u"This is my article", content=u"<p>This is my <b>content</b></p>",
            template = settings.COOP_CMS_ARTICLE_TEMPLATES[template_index][0])
        if image:
            a.logo = File(self._get_file())
            a.save()
        
        response = self.client.get(a.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, a.title)
        self.assertContains(response, a.content)
        
    def test_view_article_no_image_crop(self):
        self.test_view_article_no_image(1)
        
    def test_view_article_image_no_crop(self):
        self.test_view_article_no_image(0, True)
        
    def test_view_article_image_and_crop(self):
        self.test_view_article_no_image(1, True)
        
    def test_edit_article_no_image(self, template_index=0, image=False, post_image=False):
        Article = get_article_class()
        if image:
            a = mommy.make(Article,
                title=u"This is my article", content=u"<p>This is my <b>content</b></p>", slug="",
                template = settings.COOP_CMS_ARTICLE_TEMPLATES[template_index][0], logo=File(self._get_file())
            )
        else:
            a = mommy.make(Article,
                title=u"This is my article", content=u"<p>This is my <b>content</b></p>", slug="",
                template = settings.COOP_CMS_ARTICLE_TEMPLATES[template_index][0]
            )
            
        self._log_as_editor()
        
        response = self.client.post(a.get_edit_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        
        data = {
            'title': 'Title of the article',
            'content': 'The content',
        }
        if post_image:
            data['logo'] = self._get_file('unittest2.png')
        response = self.client.post(a.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a = Article.objects.get(id=a.id)
        
        self.assertEqual(data['title'], a.title)
        self.assertEqual(data['content'], a.content)
        
        self.assertContains(response, a.title)
        self.assertContains(response, a.content)
        
    def test_edit_article_no_image_crop(self):
        self.test_edit_article_no_image(1)
        
    def test_edit_article_image_no_post_no_crop(self):
        self.test_edit_article_no_image(0, True, False)
        
    def test_edit_article_image_no_post_crop(self):
        self.test_edit_article_no_image(1, True, False)
        
    def test_edit_article_image_post_no_crop(self):
        self.test_edit_article_no_image(0, True, True)
        
    def test_edit_article_image_post_crop(self):
        self.test_edit_article_no_image(1, True, True)
    
    def test_view_article_no_image_template1(self):
        self.test_view_article_no_image(2, False)
        
    def test_view_article_no_image_template2(self):
        self.test_view_article_no_image(2, True)
        
    def test_view_article_no_image_template3(self):
        settings.COOP_CMS_ARTICLE_LOGO_SIZE = "x100"
        settings.COOP_CMS_ARTICLE_LOGO_CROP = "top"
        self.test_view_article_no_image(2, True)
        
    def test_edit_article_no_image_template1(self):
        self.test_edit_article_no_image(2, False, False)
        
    def test_edit_article_no_image_template2(self):
        self.test_edit_article_no_image(2, True, False)
        
    def test_edit_article_no_image_template3(self):
        self.test_edit_article_no_image(2, True, True)
        
    def test_edit_article_no_image_template4(self):
        settings.COOP_CMS_ARTICLE_LOGO_SIZE = "x100"
        settings.COOP_CMS_ARTICLE_LOGO_CROP = "top"
        self.test_edit_article_no_image(2, True, True)
    
        
class BlockInheritanceTest(BaseArticleTest):
    
    def setUp(self):
        super(BlockInheritanceTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article_with_blocks.html', 'Article with blocks'),
        )
        
    def tearDown(self):
        super(BlockInheritanceTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates

    def test_view_with_blocks(self):
        Article = get_article_class()
        a = mommy.make(Article,
            title=u"This is my article", content=u"<p>This is my <b>content</b></p>",
            template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0])
        
        response = self.client.get(a.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, a.title)
        self.assertContains(response, a.content)
        
        self.assertContains(response, "*** HELLO FROM CHILD ***")
        self.assertContains(response, "*** HELLO FROM PARENT ***")
        self.assertContains(response, "*** HELLO FROM BLOCK ***")
        
    def test_edit_with_blocks(self):
        Article = get_article_class()
        a = mommy.make(Article,
            title=u"This is my article", content=u"<p>This is my <b>content</b></p>",
            template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0])
        
        self._log_as_editor()
        
        data = {
            "title": u"This is a new title", 
            'content': "<p>This is a <i>*** NEW ***</i> <b>content</b></p>"
        }
        response = self.client.post(a.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a = Article.objects.get(id=a.id)
        
        self.assertEqual(a.title, data['title'])
        self.assertEqual(a.content, data['content'])
        
        self.assertContains(response, a.title)
        self.assertContains(response, a.content)
        
        self.assertContains(response, "*** HELLO FROM CHILD ***")
        self.assertContains(response, "*** HELLO FROM PARENT ***")
        self.assertContains(response, "*** HELLO FROM BLOCK ***")

class PermissionMiddlewareTest(BaseArticleTest):
    
    def setUp(self):
        super(PermissionMiddlewareTest, self).setUp()
        self._MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES
        if not 'coop_cms.middleware.PermissionsMiddleware' in settings.MIDDLEWARE_CLASSES:
            settings.MIDDLEWARE_CLASSES += ('coop_cms.middleware.PermissionsMiddleware',)
        
    def tearDown(self):
        super(PermissionMiddlewareTest, self).tearDown()
        self.MIDDLEWARE_CLASSES = self._MIDDLEWARE_CLASSES
        
    def test_view_draft_anonymous(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.DRAFT)
        self.assertEqual(article.is_draft(), True)
        url = article.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        auth_url = reverse(AUTH_LOGIN_NAME)
        self.assertRedirects(response, auth_url+'?next='+url)
        
    def test_edit_anonymous(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.DRAFT)
        self.assertEqual(article.is_draft(), True)
        url = article.get_edit_url()
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        auth_url = reverse(AUTH_LOGIN_NAME)
        self.assertEqual(response["Location"], "http://testserver"+auth_url+'?next='+url)
        #self.assertRedirects(response, auth_url+'?next='+url)
        
    def test_view_published_anonymous(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        self.assertEqual(article.is_draft(), False)
        url = article.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
    def test_view_draft_not_allowed(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.DRAFT)
        self.assertEqual(article.is_draft(), True)
        
        self._log_as_non_editor()
        
        url = article.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)
        
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
        
class MultiSiteTest(BaseArticleTest):
    
    def setUp(self):
        self.settings_site_id = settings.SITE_ID
        settings.SITE_ID = 1
        
    def tearDown(self):
         settings.SITE_ID = self.settings_site_id
    
    def test_article_category_other_site(self):
        Article = get_article_class()
        site1 = Site.objects.get(id=settings.SITE_ID)
        site2 = mommy.make(Site)
        
        cat = mommy.make(ArticleCategory)
        
        art1 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED)
        
        art2 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED,
            publication_date=art1.publication_date+timedelta(1))
        art2.sites.add(site2)
        art2.sites.remove(site1)
        art2.save()
        
        art3 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED,
            publication_date=art1.publication_date-timedelta(1))
        art3.sites.add(site2)
        art3.sites.remove(site1)
        art3.save()
        
        self.assertEqual(art1.previous_in_category(), None)
        self.assertEqual(art1.next_in_category(), None)
        
    def test_article_category_same_site(self):
        Article = get_article_class()
        site1 = Site.objects.get(id=settings.SITE_ID)
        site2 = mommy.make(Site)
        
        cat = mommy.make(ArticleCategory)
        
        art1 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED)
        
        art2 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED,
            publication_date=art1.publication_date+timedelta(1))
        
        art3 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED,
            publication_date=art1.publication_date-timedelta(1))
        art3.sites.add(site2)
        art3.save()
        
        self.assertEqual(art1.previous_in_category(), art3)
        self.assertEqual(art1.next_in_category(), art2)
        
    def test_article_category_not_published(self):
        Article = get_article_class()
        site1 = Site.objects.get(id=settings.SITE_ID)
        site2 = mommy.make(Site)
        
        cat = mommy.make(ArticleCategory)
        
        art1 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED)
        
        art2 = mommy.make(Article, category=cat, publication=BaseArticle.DRAFT,
            publication_date=art1.publication_date+timedelta(1))
        
        art3 = mommy.make(Article, category=cat, publication=BaseArticle.DRAFT,
            publication_date=art1.publication_date-timedelta(1))
        art3.sites.add(site2)
        art3.save()
        
        self.assertEqual(art1.previous_in_category(), None)
        self.assertEqual(art1.next_in_category(), None)
        
    def test_article_category(self, ):
        self._log_as_editor()
        
        Article = get_article_class()
        site1 = Site.objects.get(id=settings.SITE_ID)
        site2 = mommy.make(Site)
        
        cat = mommy.make(ArticleCategory)
        self.assertEqual(list(cat.sites.all()), [site1])
        
        cat2 = mommy.make(ArticleCategory)
        cat2.sites.remove(site1)
        cat2.sites.add(site2)
        cat2.save()
        self.assertEqual(list(cat2.sites.all()), [site2])
        
        cat3 = mommy.make(ArticleCategory)
        cat3.sites.remove(site1)
        cat3.save()
        self.assertEqual(list(cat3.sites.all()), [])
        
        art1 = mommy.make(Article, category=cat, publication=BaseArticle.PUBLISHED)
        
        url = reverse('coop_cms_article_settings', args=[art1.id])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        cat_choices = soup.select("select#id_category option")
        self.assertEqual(2, len(cat_choices))
        self.assertEqual("", cat_choices[0]["value"])
        self.assertEqual(str(cat.id), cat_choices[1]["value"])
        self.assertEqual(cat.name, cat_choices[1].text)
        
    
    