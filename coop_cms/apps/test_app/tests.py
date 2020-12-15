# -*- coding: utf-8 -*-

from django.conf import settings

from datetime import datetime
import logging

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings

from model_mommy import mommy

from coop_cms.apps.test_app.models import TestClass, TestTag
from coop_cms import settings as coop_settings
from coop_cms.models import BaseArticle, Newsletter
from coop_cms.tests import BeautifulSoup, BaseArticleTest
from coop_cms.tests.test_newsletter import NewsletterSettingsTest
from coop_cms.utils import get_login_url


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
        
        content_type = ContentType.objects.get_for_model(TestClass)
        
        perm = 'change_{0}'.format(content_type.model)
        can_edit = Permission.objects.get(content_type=content_type, codename=perm)
        user.user_permissions.add(can_edit)
        
        perm = 'add_{0}'.format(content_type.model)
        can_add = Permission.objects.get(content_type=content_type, codename=perm)
        user.user_permissions.add(can_add)
        
        user.is_active = True
        user.is_staff = True  # can_edit_object
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
            auth_url = get_login_url()
            self.assertRedirects(response, auth_url + '?next=' + url)
        else:
            self.assertEqual(403, response.status_code)

    def test_edit_object_anonymous(self):
        obj = mommy.make(TestClass)
        url = obj.get_edit_url()
        
        response = self.client.get(url)
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = get_login_url()
            self.assertRedirects(response, auth_url + '?next=' + url)
        else:
            self.assertEqual(403, response.status_code)
        
        field1, field2 = obj.field1, obj.field2
        data = {'field1': "ABC", 'field2': "DEF", 'bool_field': True, 'int_field': 2, 'float_field': 3.14}
        response = self.client.post(url, data=data)
        
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = get_login_url()
            self.assertRedirects(response, auth_url + '?next=' + url)
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
        soup = BeautifulSoup(response.content)
        self.assertEqual("ABC", soup.select("#properties")[0].text)
        
    def test_view_object_viewer_bool_true(self):
        self._log_as_viewer()
        obj = mommy.make(TestClass, bool_field=True)
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select(".bool_field_is_true")))
        self.assertEqual(0, len(soup.select(".bool_field_is_false")))

    def test_view_object_m2m_relationships(self):
        self._log_as_viewer()
        obj = mommy.make(TestClass)
        tag1 = mommy.make(TestTag, name='The-Tag-1#')
        tag2 = mommy.make(TestTag, name='The-Tag-2#')
        tag3 = mommy.make(TestTag, name='The-Tag-3#')
        obj.tags.add(tag1)
        obj.tags.add(tag2)
        obj.save()
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, tag1.name)
        self.assertContains(response, tag2.name)
        self.assertNotContains(response, tag3.name)

    def test_view_object_viewer_bool_false(self):
        self._log_as_viewer()
        obj = mommy.make(TestClass, bool_field=False)
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        self.assertEqual(0, len(soup.select(".bool_field_is_true")))
        self.assertEqual(1, len(soup.select(".bool_field_is_false")))
    
    def test_edit_object_viewer(self):
        self._log_as_viewer()
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_edit_url())
        self.assertEqual(403, response.status_code)
        
        field1, field2 = obj.field1, obj.field2
        
        data = {'field1': "ABC", 'field2': "DEF", 'bool_field': True, 'int_field': 2, 'float_field': 3.14}
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
        
        data = {'field1': "ABC", 'field2': "DEF", 'bool_field': True, 'int_field': 2, 'float_field': 3.14}
        response = self.client.post(obj.get_edit_url(), data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertEqual(obj.field1, data["field1"])
        self.assertEqual(obj.field2, data["field2"])
        self.assertEqual(obj.bool_field, data["bool_field"])
        self.assertEqual(obj.int_field, data["int_field"])
        self.assertEqual(obj.float_field, data["float_field"])

    def test_edit_object_inactive(self):
        self._log_as_editor()
        self.editor.is_active = False
        self.editor.save()
        
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_edit_url())
        self.assertEqual(403, response.status_code)
        
        data = {'field1': "ABC", 'field2': "DEF", 'bool_field': True, 'int_field': 2, 'float_field': 3.14}
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
        
        soup = BeautifulSoup(response.content)
        self.assertEqual(0, len(soup.select('form')))
        
    def test_edit_formset_no_objects(self):
        self._log_as_editor()
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select('form')))
    
    def test_view_formset_one_object(self):
        self._log_as_viewer()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset')
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        self.assertEqual(0, len(soup.select('form')))
        
        self.assertContains(response, obj.field1)
        self.assertContains(response, obj.field2)
        self.assertContains(response, obj.other_field)
        
    #def test_edit_formset_one_object(self):
    #    self._log_as_viewer()
    #    
    #    obj = mommy.make(TestClass)
    #    
    #    url = reverse('coop_cms_testapp_formset_edit')
    #    
    #    response = self.client.get(url)
    #    self.assertEqual(200, response.status_code)
    #    
    #    soup = BeautifulSoup(response.content)
    #    self.assertEqual(1, len(soup.select('form')))
    #    
    #    print response.content
    #    
    #    self.assertContains(response, obj.field1)
    #    self.assertContains(response, obj.field2)
    #    self.assertContains(response, obj.other_field)
        
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
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        data = {
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
    def test_post_formset_on_view(self):
        self._log_as_editor()
        
        url = reverse('coop_cms_testapp_formset')
        
        data = {
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(404, response.status_code)
        
    def test_post_edit_formset_one_object(self):
        self._log_as_editor()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            #'form-0-field3': "",
            'form-0-other_field': "wxcvbn",
            'form-0-bool_field': True,
            'form-0-int_field': 2,
            'form-0-float_field': 3.14,
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
        self.assertEqual(data['form-0-bool_field'], obj.bool_field)
        self.assertEqual(data['form-0-int_field'], obj.int_field)
        self.assertEqual(data['form-0-float_field'], obj.float_field)
        
    def test_edit_formset_several_object(self):
        self._log_as_editor()
        
        obj1 = mommy.make(TestClass)
        obj2 = mommy.make(TestClass)
        
        data = {
            'form-0-id': obj1.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-field3': "AZDD",
            'form-0-bool_field': True,
            'form-0-int_field': 2,
            'form-0-float_field': 3.14,
            'form-1-id': obj2.id,
            'form-1-field1': "POIUYTREZA",
            'form-1-field2': "<p>MLKJHGFDSQ</p>",
            'form-1-field3': "QSkk",
            'form-1-bool_field': False,
            'form-1-int_field': 2,
            'form-1-float_field': 3.14,
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2,
        }
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        objects = TestClass.objects.all()
        
        for i, obj in enumerate(objects):
            self.assertEqual(data['form-{0}-field1'.format(i)], obj.field1)
            self.assertEqual(data['form-{0}-field2'.format(i)], obj.field2)
            self.assertEqual(data['form-{0}-field3'.format(i)], obj.field3)
            self.assertEqual(data['form-{0}-bool_field'.format(i)], obj.bool_field)
            self.assertEqual(data['form-{0}-int_field'.format(i)], obj.int_field)
            self.assertEqual(data['form-{0}-float_field'.format(i)], obj.float_field)
            
    def test_edit_formset_extra_1(self):
        self._log_as_editor()
        
        obj1 = mommy.make(TestClass)
        
        data = {
            'form-0-id': obj1.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-field3': "AZDD",
            'form-0-bool_field': True,
            'form-0-int_field': 2,
            'form-0-float_field': 3.14,
            'form-1-id': '',
            'form-1-field1': "POIUYTREZA",
            'form-1-field2': "<p>MLKJHGFDSQ</p>",
            'form-1-field3': "QSkk",
            'form-1-bool_field': True,
            'form-1-int_field': 2,
            'form-1-float_field': 3.14,
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 2,
        }
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        objects = TestClass.objects.all()
        
        self.assertEqual(2, objects.count())
        
        for i, obj in enumerate(objects):
            self.assertEqual(data['form-{0}-field1'.format(i)], obj.field1)
            self.assertEqual(data['form-{0}-field2'.format(i)], obj.field2)
            self.assertEqual(data['form-{0}-field3'.format(i)], obj.field3)
            self.assertEqual(data['form-{0}-bool_field'.format(i)], obj.bool_field)
            self.assertEqual(data['form-{0}-int_field'.format(i)], obj.int_field)
            self.assertEqual(data['form-{0}-float_field'.format(i)], obj.float_field)
    
    def test_edit_formset_anonymous(self):
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-bool_field': True,
            'form-0-int_field': 2,
            'form-0-float_field': 3.14,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1,
        }
        
        response = self.client.post(url, data=data)
        
        if coop_settings.is_perm_middleware_installed():
            self.assertEqual(302, response.status_code)
            auth_url = get_login_url()
            self.assertRedirects(response, auth_url+'?next='+url)
        else:
            self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        
        self.assertNotEqual(data['form-0-field1'], obj.field1)
        self.assertNotEqual(data['form-0-field2'], obj.field2)
        
    def test_edit_formset_viewer(self):
        self._log_as_viewer()
        
        obj = mommy.make(TestClass)
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-bool_field': True,
            'form-0-int_field': 2,
            'form-0-float_field': 3.14,
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
        
        url = reverse('coop_cms_testapp_formset_edit')
        
        other_field = obj.other_field
        data = {
            'form-0-id': obj.id,
            'form-0-field1': "AZERTYUIOP",
            'form-0-field2': "<p>QWERTY/nUIOP</p>",
            'form-0-bool_field': True,
            'form-0-int_field': 2,
            'form-0-float_field': 3.14,
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
            if v is None:
                self._settings_backup[s] = v
        
        self.LOGIN_URL = settings.LOGIN_URL
        settings.LOGIN_URL = get_login_url()
        settings.COOP_CMS_NEW_ARTICLE_FORM = 'coop_cms.apps.test_app.forms.MyNewArticleForm'
        settings.COOP_CMS_ARTICLE_SETTINGS_FORM = 'coop_cms.apps.test_app.forms.MyArticleSettingsForm'
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article.html', 'Article'),
            ('test/article_with_blocks.html', 'Article with blocks'),
        )

        super(ArticleFormTest, self).setUp()
        
    def tearDown(self):
        for setting in self._settings_fields_to_backup():
            value = self._settings_backup.get(setting, None)
            if value is not None:
                setattr(settings, setting, value)
        
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
        auth_url = get_login_url()
        self.assertRedirects(response, auth_url+'?next='+url)

    def test_view_article_not_allowed(self):
        self._log_as_viewer()
        article_class = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(article_class.objects.count(), 0)
    
    def test_new_article(self):
        self._log_as_editor()
        article_class = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        data = {
            'title': 'test',
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'navigation_parent': '',
            'sites': [settings.SITE_ID]
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        for field in data:
            if field == "sites":
                self.assertEqual([x.id for x in getattr(article, field).all()], data[field])
            elif field == "navigation_parent":
                self.assertEqual(getattr(article, field), None)
            else:
                self.assertEqual(getattr(article, field), data[field])

    def test_new_article_anoymous(self):
        article_class = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        data = {
            'title': 'test',
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'navigation_parent': '',
            'sites': [settings.SITE_ID],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        login_url = get_login_url()
        self.assertTrue(response['Location'].find(login_url) >= 0)
        
        self.assertEqual(article_class.objects.count(), 0)
        
    def test_new_article_not_allowed(self):
        self._log_as_viewer()
        article_class = coop_settings.get_article_class()
        url = reverse('coop_cms_new_article')
        data = {
            'title': 'test',
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'navigation_parent': '',
            'sites': [settings.SITE_ID],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        
        self.assertEqual(article_class.objects.count(), 0)
        
    def test_view_article_settings(self):
        self._log_as_editor()
        article_class = coop_settings.get_article_class()
        article = mommy.make(article_class, slug="test")
        url = reverse('coop_cms_article_settings', args=[article.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("#id_dummy")))
    
    def test_view_article_settings_anonymous(self):
        article_class = coop_settings.get_article_class()
        article = mommy.make(article_class, slug="test")
        url = reverse('coop_cms_article_settings', args=[article.id])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        auth_url = get_login_url()
        self.assertRedirects(response, auth_url+'?next='+url)
        
    def test_view_article_settings_not_allowed(self):
        self._log_as_viewer()
        article_class = coop_settings.get_article_class()
        article = mommy.make(article_class, slug="test")
        url = reverse('coop_cms_article_settings', args=[article.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(article_class.objects.count(), 1)
    
    def test_article_settings(self):
        self._log_as_editor()
        article_class = coop_settings.get_article_class()
        article = mommy.make(article_class, slug="test")
        url = reverse('coop_cms_article_settings', args=[article.id])
        
        now = datetime.now()
        now = now.replace(microsecond=0)
        data = {
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication_date': now,
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'summary': 'Summary',
            'navigation_parent': '',
            'sites': [settings.SITE_ID],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        for field in data:
            if field == "sites":
                self.assertEqual([x.id for x in getattr(article, field).all()], data[field])
            elif field == "navigation_parent":
                self.assertEqual(article.navigation_parent, None)
            else:
                self.assertEqual(getattr(article, field), data[field])
        
    def test_article_settings_anonymous(self):
        article_class = coop_settings.get_article_class()
        article = mommy.make(article_class, slug="test")
        url = reverse('coop_cms_article_settings', args=[article.id])
        
        data = {
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication_date': datetime.now(),
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'summary': 'Summary',
            'navigation_parent': '',
            'sites': [settings.SITE_ID],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        login_url = get_login_url()
        self.assertTrue(response['Location'].find(login_url) >= 0)
        
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertNotEqual(article.summary, data['summary'])
        
    def test_article_settings_not_allowed(self):
        self._log_as_viewer()
        article_class = coop_settings.get_article_class()
        article = mommy.make(article_class, slug="test")
        url = reverse('coop_cms_article_settings', args=[article.id])
        
        data = {
            'template': settings.COOP_CMS_ARTICLE_TEMPLATES[0][0],
            'publication_date': datetime.now(),
            'publication': BaseArticle.PUBLISHED,
            'in_newsletter': False,
            'summary': 'Summary',
            'navigation_parent': '',
            'sites': [settings.SITE_ID],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        
        self.assertEqual(article_class.objects.count(), 1)
        article = article_class.objects.all()[0]
        self.assertNotEqual(article.summary, data['summary'])


class MyNewsletterSettingsTest(NewsletterSettingsTest):

    @override_settings(COOP_CMS_NEWSLETTER_SETTINGS_FORM="coop_cms.apps.test_app.forms.MyNewsletterSettingsForm")
    def test_additional_field_on_edit(self):
        self._log_as_editor()
        newsletter = mommy.make(
            Newsletter,
            subject="a little intro for this newsletter",
            template="test/newsletter_blue.html",
        )

        url = reverse("coop_cms_newsletter_settings", args=[newsletter.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("#id_dummy")))

    @override_settings(COOP_CMS_NEWSLETTER_SETTINGS_FORM="coop_cms.apps.test_app.forms.MyNewsletterSettingsForm")
    def test_additional_field_on_create(self):
        self._log_as_editor()

        url = reverse("coop_cms_new_newsletter")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("#id_dummy")))


@override_settings(COOP_CMS_ARTICLE_TEMPLATES=(('coop_cms/test_app/custom_tag_template.html', 'Custom Tag'),))
class CustomTemplateTagInCmsEditTag(BaseArticleTest):
    """test using custom templatetag inside the cms_edit template tag"""

    def test_view_with_blocks(self):
        """test view article with block templatetag inside the cms_edit template tag"""

        article_class = coop_settings.get_article_class()
        article = mommy.make(
            article_class,
            title="This is my article", content="<p>This is my <b>content</b></p>",
            template='coop_cms/test_app/custom_tag_template.html'
        )

        response = self.client.get(article.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content)

        self.assertEqual(3, len(soup.select("ul.custom li")))

        self.assertContains(response, article.title)
        self.assertContains(response, article.content)

        self.assertContains(response, "*** HELLO FROM CHILD ***")
        self.assertContains(response, "*** HELLO FROM PARENT ***")
        self.assertContains(response, "*** HELLO FROM BLOCK ***")

    def test_edit_with_blocks(self):
        """test edition with block templatetag inside the cms_edit template tag"""

        article_class = coop_settings.get_article_class()
        article = mommy.make(
            article_class,
            title="This is my article", content="<p>This is my <b>content</b></p>",
            template='coop_cms/test_app/custom_tag_template.html'
        )

        self._log_as_editor()

        data = {
            "title": "This is a new title",
            'content': "<p>This is a <i>*** NEW ***</i> <b>content</b></p>"
        }
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        article = article_class.objects.get(id=article.id)

        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.content, data['content'])

        self.assertContains(response, article.title)
        self.assertContains(response, article.content)

        self.assertContains(response, "*** HELLO FROM CHILD ***")
        self.assertContains(response, "*** HELLO FROM PARENT ***")
        self.assertContains(response, "*** HELLO FROM BLOCK ***")
