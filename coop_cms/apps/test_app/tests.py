# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.template import Template, Context
from model_mommy import mommy
from django.conf import settings
from models import TestClass
import logging

class GenericViewTestCase(TestCase):
    
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
        
        data = {'field1': "ABC", 'field2': "DEF"}
        response = self.client.post(obj.get_edit_url(), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertEqual(obj.field1, "")
        self.assertEqual(obj.field2, "")
        
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
        
        data = {'field1': "ABC", 'field2': "DEF"}
        response = self.client.post(obj.get_edit_url(), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        
        obj = TestClass.objects.get(id=obj.id)
        self.assertEqual(obj.field1, "")
        self.assertEqual(obj.field2, "")
        
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
        
        
