# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()
    
from django.test import TestCase
from model_mommy import mommy
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from bs4 import BeautifulSoup
from django.test.utils import override_settings

TEST_AUTHENTICATION_BACKENDS = (
    'coop_cms.perms_backends.ArticlePermissionBackend',
    'coop_cms.apps.email_auth.auth_backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend', # Django's default auth backend
)

class BaseTest(TestCase):
    
    def _make(self, klass, **kwargs):
        password = None
        if klass==User:
            password = kwargs.pop('password', None)
        obj = mommy.make(klass, **kwargs)
        if password:
            obj.set_password(password)
            obj.save()
        return obj
    

@override_settings(AUTHENTICATION_BACKENDS=TEST_AUTHENTICATION_BACKENDS)
class EmailAuthBackendTest(BaseTest):
    
    def test_email_login(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        login_ok = self.client.login(email=user.email, password="password")
        self.assertEqual(login_ok, True)
    
    def test_email_login_inactve(self):
        user = self._make(User, is_active=False, password="password", email="toto@toto.fr", username="toto")
        login_ok = self.client.login(email=user.email, password="password")
        self.assertEqual(login_ok, False)
    
    def test_email_login_not_exists(self):
        login_ok = self.client.login(email="titi@titi.fr", password="password")
        self.assertEqual(login_ok, False)
    
    def test_email_login_several(self):
        user1 = self._make(User, is_active=True, password="password1", email="toto@toto.fr", username="toto1")
        user2 = self._make(User, is_active=True, password="password2", email="toto@toto.fr", username="toto2")
        login_ok = self.client.login(email=user1.email, password="password1")
        self.assertEqual(login_ok, True)
        self.client.logout()
        login_ok = self.client.login(email=user2.email, password="password2")
        self.assertEqual(login_ok, True)
    
    def test_email_login_wrong_password(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        login_ok = self.client.login(email=user.email, password="toto")
        self.assertEqual(login_ok, False)    
  
@override_settings(AUTHENTICATION_BACKENDS=TEST_AUTHENTICATION_BACKENDS)      
class UserLoginTest(BaseTest):

    def test_view_login(self):
        url = reverse("login")
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        self.assertTrue(len(soup.select("input[name=email]"))>0)
        self.assertTrue(len(soup.select("input[name=password]"))>0)
        self.assertEqual(0, len(soup.select("input[name=username]")))
        
    def test_post_login(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password',
            'email': user.email,
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, user.id)
    
    def test_post_login_wrong_password(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password&&',
            'email': user.email,
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    def test_post_login_wrong_email(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password',
            'email': 'toto@toto.com',
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    def test_post_login_invalid_email(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password',
            'email': "a",
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    def test_post_login_missing_password(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': '',
            'email': user.email,
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    def test_post_login_missing_email(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password',
            'email': '',
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
        
    def test_post_login_missing_both(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': '',
            'email': "",
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    def test_post_login_inactive_user(self):
        user = self._make(User, is_active=False, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password',
            'email': user.email,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    def test_post_login_username(self):
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
    
        url = reverse("login")
        
        data = {
            'password': 'password',
            'username': user.username,
        }
        
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(user_id, 0)
    
    