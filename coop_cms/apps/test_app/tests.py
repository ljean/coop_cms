# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.template import Template, Context
from model_mommy import mommy
from django.conf import settings
from models import TestClass
import logging

class BaseTestCase(TestCase):
    
    def setUp(self):
        logging.disable(logging.CRITICAL)
        
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _log_as_viewer(self):
        self.viewer = user = User.objects.create_user('viewer', 'viewer@toto.fr', 'viewer')
        return self.client.login(username='viewer', password='viewer')
        
    def _log_as_editor(self):
        self.editor = User.objects.create_user('editor', 'toto@toto.fr', 'editor')
        self.editor.is_staff = True
        self.editor.save()
        return self.client.login(username='editor', password='editor')
  

class GenericViewTestCase(BaseTestCase):
    
    def test_view_list_objects(self):
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_list_url())
        self.assertEqual(200, response.status_code)
    
    def test_view_object_anomymous(self):
        obj = mommy.make(TestClass)
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(403, response.status_code)
    
    def test_edit_object_anonymous(self):
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
        
    def test_view_formset_seeveral_object(self):
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
        
        
    def test_edit_formset_seeveral_object(self):
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
        
        response = self.client.post(url, data=data, follow=True)
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
