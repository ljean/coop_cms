
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
from model_mommy import mommy
from django.conf import settings
from models import TestClass
import logging
from coop_cms import settings as coop_settings
from coop_cms.models import BaseArticle
from bs4 import BeautifulSoup
from datetime import datetime

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
    
    def _log_as_viewer(self):
        self.viewer = user = User.objects.create_user('viewer', 'viewer@toto.fr', 'viewer')
        return self.client.login(username='viewer', password='viewer')
    
    def _log_as_editor(self):
        self.editor = user = User.objects.create_user('editor', 'toto@toto.fr', 'editor')
        
        ct = ContentType.objects.get_for_model(TestClass)
        
        perm = 'change_{0}'.format(ct.model)
        can_edit = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit)
        
        perm = 'add_{0}'.format(ct.model)
        can_add = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add)
        
        user.is_active = True
        user.is_staff = True #can_edit_object
        #user.user_permissions
        user.save()
        return self.client.login(username='editor', password='editor')
  

class GenericViewTestCase(BaseTestCase):
    
    def test_view_list_objects(self):
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_list_url())
        self.assertEqual(200, response.status_code)
    
    def test_view_object_anomymous(self):
        obj = mommy.make(TestClass)
        url = obj.get_absolute_url()
        response = self.client.get(url)
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
    
    def test_edit_object_anonymous(self):
        obj = mommy.make(TestClass)
        url = obj.get_edit_url()
        
        response = self.client.get(url)
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
        field1, field2 = obj.field1, obj.field2
        data = {'field1': "ABC", 'field2': "DEF"}
        response = self.client.post(url, data=data)
        
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertEqual(obj.field1, field1)
        self.assertEqual(obj.field2, field2)
        
    def test_view_object_viewer(self):
        self._log_as_viewer()
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(200, response.status_code)
    
    def test_edit_object_viewer(self):
        self._log_as_viewer()
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_edit_url())
        self.assertEqual(403, response.status_code)
        
        field1, field2 = obj.field1, obj.field2
        
        data = {'field1': "ABC", 'field2': "DEF"}
        response = self.client.post(obj.get_edit_url(), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertEqual(obj.field1, field1)
        self.assertEqual(obj.field2, field2)
        
    def test_view_object_editor(self):
        self._log_as_editor()
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(200, response.status_code)
    
    def test_edit_object_editor(self):
        self._log_as_editor()
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_edit_url())
        self.assertEqual(200, response.status_code)
        
        data = {'field1': "ABC", 'field2': "DEF"}
        response = self.client.post(obj.get_edit_url(), data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertEqual(obj.field1, data["field1"])
        self.assertEqual(obj.field2, data["field2"])
        
    def test_edit_object_inactive(self):
        self._log_as_editor()
        self.editor.is_active = False
        self.editor.save()
        
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_edit_url())
        self.assertEqual(403, response.status_code)
        
        data = {'field1': "ABC", 'field2': "DEF"}
        response = self.client.post(obj.get_edit_url(), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertNotEqual(obj.field1, data["field1"])
        self.assertNotEqual(obj.field2, data["field2"])
        
        
class FormsetViewTestCase(BaseTestCase):
    
    def test_view_formset_no_objects(self):
        self._log_as_viewer()
        
        url = reverse('coop_cms_testapp_formset')
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
    def test_view_formset_one_object(self):
        self._log_as_viewer()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset')
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, obj.field1)
        self.assertContains(response, obj.field2)
        self.assertContains(response, obj.other_field)
        
    def test_view_formset_several_object(self):
        self._log_as_viewer()
        
        obj1 = mommy.make(TestClass)
        obj2 = mommy.make(TestClass)
        obj3 = mommy.make(TestClass)
        
        objects = [obj1, obj2, obj3]
        
        url = reverse('coop_cms_testapp_formset')
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        for obj in objects:
            self.assertContains(response, obj.field1)
            self.assertContains(response, obj.field2)
            self.assertContains(response, obj.other_field)

    def test_edit_formset_no_objects(self):
        self._log_as_editor()
        
        url = reverse('coop_cms_testapp_formset')
        
        data = {
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
    def test_edit_formset_one_object(self):
        self._log_as_editor()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            #'form-0-field3': "",
            'form-0-other_field': "wxcvbn",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        
        self.assertContains(response, obj.field1)
        self.assertContains(response, obj.field2)
        self.assertContains(response, other_field)
        
        self.assertEqual(data['form-0-field1'], obj.field1)
        self.assertEqual(data['form-0-field2'], obj.field2)
        self.assertEqual(other_field, obj.other_field)
        
        
    def test_edit_formset_several_object(self):
        self._log_as_editor()
        
        obj1 = mommy.make(TestClass)
        obj2 = mommy.make(TestClass)
        
        data = {
            'form-0-id': obj1.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-field3': "AZDD",
            'form-1-id': obj2.id,
            'form-1-field1': "POIUYTREZA",
            'form-1-field2': "<p>MLKJHGFDSQ</p>",
            'form-1-field3': "QSkk",
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2,
        }
        
        url = reverse('coop_cms_testapp_formset')
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        objects = TestClass.objects.all()
        
        for i, obj in enumerate(objects):
            self.assertEqual(data['form-{0}-field1'.format(i)], obj.field1)
            self.assertEqual(data['form-{0}-field2'.format(i)], obj.field2)
            self.assertEqual(data['form-{0}-field3'.format(i)], obj.field3)
            
    def test_edit_formset_extra_1(self):
        self._log_as_editor()
        
        obj1 = mommy.make(TestClass)
        
        data = {
            'form-0-id': obj1.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-field3': "AZDD",
            'form-1-id': '',
            'form-1-field1': "POIUYTREZA",
            'form-1-field2': "<p>MLKJHGFDSQ</p>",
            'form-1-field3': "QSkk",
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 2,
        }
        
        url = reverse('coop_cms_testapp_formset')
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        objects = TestClass.objects.all()
        
        self.assertEqual(2, objects.count())
        
        for i, obj in enumerate(objects):
            self.assertEqual(data['form-{0}-field1'.format(i)], obj.field1)
            self.assertEqual(data['form-{0}-field2'.format(i)], obj.field2)
            self.assertEqual(data['form-{0}-field3'.format(i)], obj.field3)
    
    def test_edit_formset_anonymous(self):
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data)
        
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = reverse(AUTH_LOGIN_NAME)
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        
        self.assertNotEqual(data['form-0-field1'], obj.field1)
        self.assertNotEqual(data['form-0-field2'], obj.field2)
        
    def test_edit_formset_viewer(self):
        self._log_as_viewer()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        
        self.assertNotEqual(data['form-0-field1'], obj.field1)
        self.assertNotEqual(data['form-0-field2'], obj.field2)
        
    def test_edit_formset_inactive(self):
        self._log_as_editor()
        self.editor.is_active = False
        self.editor.save()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        
        self.assertNotEqual(data['form-0-field1'], obj.field1)
        self.assertNotEqual(data['form-0-field2'], obj.field2)

class ArticleFormTest(BaseTestCase):
    
    def _log_as_viewer(self):
        self.viewer = user = User.objects.create_user('viewer', 'viewer@toto.fr', 'viewer')
        return self.client.login(username='viewer', password='viewer')
    
    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct = ContentType.objects.get_for_model(coop_settings.get_article_class())
        
        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)
        
        perm = 'add_{0}'.format(ct.model)
        can_add_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add_article)
        
        user.save()
        
        return self.client.login(username='toto', password='toto')
    
    def _settings_fields_to_backup(self):
        return (
            'COOP_CMS_ARTICLE_SETTINGS_FORM', 'COOP_CMS_NEW_ARTICLE_FORM', 'COOP_CMS_ARTICLE_TEMPLATES',
        )
    
    def setUp(self):
        self._settings_backup = {}
        for s in self._settings_fields_to_backup():
            v = getattr(settings, s, None)
            if v != None:
                self._settings_backup[s] = v
        
        self.LOGIN_URL = settings.LOGIN_URL
        settings.LOGIN_URL = reverse(AUTH_LOGIN_NAME)
        settings.COOP_CMS_NEW_ARTICLE_FORM = 'coop_cms.apps.test_app.forms.MyNewArticleForm'
        settings.COOP_CMS_ARTICLE_SETTINGS_FORM = 'coop_cms.apps.test_app.forms.MyArticleSettingsForm'
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article.html', 'Article'),
            ('test/article_with_blocks.html', 'Article with blocks'),
        )

        super(ArticleFormTest, self).setUp()
        
    def tearDown(self):
        for s in self._settings_fields_to_backup():
            v = self._settings_backup.get(s, None)
            if v != None:
                setattr(settings, s, v)
        
        settings.LOGIN_URL = self.LOGIN_URL
        super(ArticleFormTest, self).tearDown()

    def test_view_new_article(self):
        self._log_as_editor()
        url = reverse('coop_cms_new_article')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("#id_dummy")))
    
    def test_view_new_article_anonymous(self):
        url = reverse('coop_cms_new_article')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        auth_url = reverse(AUTH_LOGIN_NAME)
        self.assertRedirects(response, auth_url+'?next='+url)

    def test_view_article_not_allowed(self):
        self._log_as_viewer()
        Article = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Article.objects.count(), 0)
    
    def test_new_article(self):
        self._log_as_editor()
        Article = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        data = {
            'title': 'test',
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            #'category': '',
            #'headline': '',
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'navigation_parent': None
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        for f in data:
            self.assertEqual(getattr(article, f), data[f])
        
        
    def test_new_article_anoymous(self):
        Article = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        data = {
            'title': 'test',
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            #'category': '',
            #'headline': '',
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'navigation_parent': None
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        login_url = reverse(AUTH_LOGIN_NAME)
        self.assertTrue(response['Location'].find(login_url)>0)
        
        self.assertEqual(Article.objects.count(), 0)
        
    def test_new_article_not_allowed(self):
        self._log_as_viewer()
        Article = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        data = {
            'title': 'test',
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            #'category': '',
            #'headline': '',
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'navigation_parent': None
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        
        self.assertEqual(Article.objects.count(), 0)
        
        
    def test_view_article_settings(self):
        self._log_as_editor()
        Article = coop_settings.get_article_class()
        article = mommy.make(Article)
        url = reverse('coop_cms_article_settings', args=[article.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("#id_dummy")))
    
    def test_view_article_settings_anonymous(self):
        Article = coop_settings.get_article_class()
        article = mommy.make(Article)
        url = reverse('coop_cms_article_settings', args=[article.id])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        auth_url = reverse(AUTH_LOGIN_NAME)
        self.assertRedirects(response, auth_url+'?next='+url)
        
        
    def test_view_article_settings_not_allowed(self):
        self._log_as_viewer()
        Article = coop_settings.get_article_class()
        article = mommy.make(Article)
        url = reverse('coop_cms_article_settings', args=[article.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Article.objects.count(), 1)
    
    def test_article_settings(self):
        self._log_as_editor()
        Article = coop_settings.get_article_class()
        article = mommy.make(Article)
        url = reverse('coop_cms_article_settings', args=[article.id])
        
        now = datetime.now()
        now = now.replace(microsecond=0)
        data = {
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication_date': now,
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'summary': 'Summary',
            'navigation_parent': None,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        for f in data:
            self.assertEqual(getattr(article, f), data[f])
        
    def test_article_settings_anoymous(self):
        Article = coop_settings.get_article_class()
        article = mommy.make(Article)
        url = reverse('coop_cms_article_settings', args=[article.id])
        
        data = {
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication_date': datetime.now(),
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'summary': 'Summary',
            'navigation_parent': None,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        login_url = reverse(AUTH_LOGIN_NAME)
        self.assertTrue(response['Location'].find(login_url)>0)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        self.assertNotEqual(article.summary, data['summary'])
        
    def test_article_settings_not_allowed(self):
        self._log_as_viewer()
        Article = coop_settings.get_article_class()
        article = mommy.make(Article)
        url = reverse('coop_cms_article_settings', args=[article.id])
        
        data = {
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication_date': datetime.now(),
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'summary': 'Summary',
            'navigation_parent': None,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        self.assertNotEqual(article.summary, data['summary'])
