# -*- coding: utf-8 -*-
"""
Email authentication Unit tests
"""

from unittest import skipUnless

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail, management
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from model_mommy import mommy

from coop_cms.moves import is_anonymous
from coop_cms.tests import BeautifulSoup

from .models import InvalidatedUser


TEST_AUTHENTICATION_BACKENDS = (
    'coop_cms.perms_backends.ArticlePermissionBackend',
    'coop_cms.apps.email_auth.auth_backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',  # Django's default auth backend
)


class BaseTest(TestCase):
    """Base class for TestCase"""

    def _make(self, klass, **kwargs):
        """Make an object"""
        password = None
        if klass == User:
            password = kwargs.pop('password', None)
        obj = mommy.make(klass, **kwargs)
        if password:
            obj.set_password(password)
            obj.save()
        return obj


@override_settings(AUTHENTICATION_BACKENDS=TEST_AUTHENTICATION_BACKENDS)
class EmailAuthBackendTest(BaseTest):
    """Email auth test case"""

    def test_email_login(self):
        """Test user can login with email"""
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        login_ok = self.client.login(email=user.email, password="password")
        self.assertEqual(login_ok, True)

    def test_email_login_inactve(self):
        """Test user can not login if inactive"""
        user = self._make(User, is_active=False, password="password", email="toto@toto.fr", username="toto")
        login_ok = self.client.login(email=user.email, password="password")
        self.assertEqual(login_ok, False)

    def test_email_login_not_exists(self):
        """Test can not login if email does'nt exist"""
        login_ok = self.client.login(email="titi@titi.fr", password="password")
        self.assertEqual(login_ok, False)

    def test_email_login_several(self):
        """test can login if several user with same email"""
        user1 = self._make(User, is_active=True, password="password1", email="toto@toto.fr", username="toto1")
        user2 = self._make(User, is_active=True, password="password2", email="toto@toto.fr", username="toto2")
        login_ok = self.client.login(email=user1.email, password="password1")
        self.assertEqual(login_ok, True)
        self.client.logout()
        login_ok = self.client.login(email=user2.email, password="password2")
        self.assertEqual(login_ok, True)

    def test_email_login_several_one_inactive(self):
        """test user can login if several user with email and one is inactive"""
        user1 = self._make(User, is_active=False, password="password1", email="toto@toto.fr", username="toto1")
        user2 = self._make(User, is_active=False, password="password2", email="toto@toto.fr", username="toto2")
        login_ok = self.client.login(email=user1.email, password="password1")
        self.assertEqual(login_ok, False)
        self.client.logout()
        login_ok = self.client.login(email=user2.email, password="password2")
        self.assertEqual(login_ok, False)

    def test_email_login_several_all_inactive(self):
        """test user can not login if several user with email but all are inactive"""
        user1 = self._make(User, is_active=False, password="password1", email="toto@toto.fr", username="toto1")
        user2 = self._make(User, is_active=True, password="password2", email="toto@toto.fr", username="toto2")
        login_ok = self.client.login(email=user1.email, password="password1")
        self.assertEqual(login_ok, False)
        self.client.logout()
        login_ok = self.client.login(email=user2.email, password="password2")
        self.assertEqual(login_ok, True)

    def test_email_login_wrong_password(self):
        """test user can not login if wrong password"""
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        login_ok = self.client.login(email=user.email, password="toto")
        self.assertEqual(login_ok, False)


@override_settings(AUTHENTICATION_BACKENDS=TEST_AUTHENTICATION_BACKENDS)
class UserLoginTest(BaseTest):
    """Test the login page"""

    def test_view_login(self):
        """test the user can view the login page"""
        url = reverse("login")
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        self.assertTrue(len(soup.select("input[name=email]")) > 0)
        self.assertTrue(len(soup.select("input[name=password]")) > 0)
        self.assertEqual(0, len(soup.select("input[name=username]")))

    def test_post_login(self):
        """test the user can login from login page"""
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        url = reverse("login")

        data = {
            'password': 'password',
            'email': user.email,
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        user_id = self.client.session.get("_auth_user_id", 0)
        self.assertEqual(int(user_id), user.id)

    def test_post_login_wrong_password(self):
        """test error if user login from the login page: wrong password"""
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
        """test error if user login from the login page: wrong email"""

        self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")

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
        """test error if user login from the login page: invalid email"""

        self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")

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
        """test error if user login from the login page: password is missing"""

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
        """test error if user login from the login page: email is missing"""

        self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")

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
        """test error if user login from the login page: user and password are missing"""

        self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")

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
        """test error if user login from the login page: inactive user"""

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
        """test error if user login from the login page: login with username"""

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


@skipUnless('django_registration' in settings.INSTALLED_APPS, "django_registration not installed installed")
@override_settings(AUTHENTICATION_BACKENDS=TEST_AUTHENTICATION_BACKENDS)
class RegistrationTest(BaseTest):
    """Test that events are sent on registration events"""

    def test_view_register(self):
        """It should display form"""
        user_count = User.objects.count()
        url = reverse('registration_register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(len(mail.outbox), 0)

        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select("input#id_email")), 1)
        self.assertEqual(len(soup.select("input#id_password1")), 1)
        self.assertEqual(len(soup.select("input#id_password2")), 1)
        self.assertEqual(len(soup.select("input#id_username")), 1)
        self.assertEqual(len(soup.select("input#id_terms_of_service")), 1)

        self.assertEqual(soup.select("input#id_email")[0]['type'], 'email')
        self.assertEqual(soup.select("input#id_password1")[0]['type'], 'password')
        self.assertEqual(soup.select("input#id_password2")[0]['type'], 'password')
        self.assertEqual(soup.select("input#id_username")[0]['type'], 'hidden')
        self.assertEqual(soup.select("input#id_terms_of_service")[0]['type'], 'checkbox')

    def test_register(self):
        """It should create disabled user"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': 'blabla-123',
            'password2': 'blabla-123',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(email=data['email']).count(), 1)
        user = User.objects.filter(email=data['email'])[0]
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [data['email']])

    def test_register_refuse_terms(self):
        """It should display error"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': 'blabla-123',
            'password2': 'blabla-123',
            'terms_of_service': False,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select('.errorlist')), 1)
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_register_refuse_wrong_password(self):
        """It should display error"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': 'blabla-123',
            'password2': 'blabla-124',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select('.errorlist')), 1)
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_register_refuse_no_password(self):
        """It should display error"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': '',
            'password2': '',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select('.errorlist')), 2)
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_register_refuse_wrong_email(self):
        """It should display error"""
        url = reverse('registration_register')
        data = {
            'email': 'john',
            'password1': 'blabla-123',
            'password2': 'blabla-123',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select('.errorlist')), 1)
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(COOP_CMS_ACCOUNT_REGISTRATION_NOTIFICATION_EMAILS=['toto@toto.fr'])
    def test_register_notify(self):
        """It should create disabled user"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': 'blabla-123',
            'password2': 'blabla-123',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(email=data['email']).count(), 1)
        user = User.objects.filter(email=data['email'])[0]
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[0]
        self.assertEqual(email.to, [data['email']])
        email = mail.outbox[1]
        self.assertEqual(email.to, ['toto@toto.fr'])
        self.assertTrue(email.body.find(data['email']) > 0)

    def test_activate_user(self):
        """It should activate the user"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': 'blabla-123',
            'password2': 'blabla-123',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        activation_key = response.context["activation_key"]

        self.assertEqual(User.objects.filter(email=data['email']).count(), 1)
        user = User.objects.filter(email=data['email'])[0]
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [data['email']])
        mail.outbox = []

        activation_url = reverse('registration_activate', args=[activation_key])
        response = self.client.get(activation_url, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(COOP_CMS_ACCOUNT_ACTION_NOTIFICATION_EMAILS=['toto@toto.fr', 'titi@titi.fr'])
    def test_activate_user_and_notify(self):
        """It should activate the user"""
        url = reverse('registration_register')
        data = {
            'email': 'john.doe@company.com',
            'password1': 'blabla-123',
            'password2': 'blabla-123',
            'terms_of_service': True,
        }
        self.assertEqual(User.objects.filter(email=data['email']).count(), 0)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        activation_key = response.context["activation_key"]

        self.assertEqual(User.objects.filter(email=data['email']).count(), 1)
        user = User.objects.filter(email=data['email'])[0]
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [data['email']])
        mail.outbox = []

        activation_url = reverse('registration_activate', args=[activation_key])
        response = self.client.get(activation_url, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['toto@toto.fr', 'titi@titi.fr'])
        self.assertTrue(email.body.find(data['email']) > 0)


@override_settings(AUTHENTICATION_BACKENDS=TEST_AUTHENTICATION_BACKENDS)
class InvalidationUserBackendTest(BaseTest):
    """check invalidated user management"""

    def test_login_user_wrong_password(self):
        """Test what happen when user with invalidated login try to login"""
        user = self._make(User, is_active=True, password="abd134", email="toto@toto.fr", username="toto")
        mommy.make(InvalidatedUser, user=user, password_changed=False)
        login_ok = self.client.login(email=user.email, password="password")
        self.assertEqual(login_ok, False)
        self.assertEqual(InvalidatedUser.objects.count(), 1)
        self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=False).count(), 1)

    def test_login(self):
        """Test user can login"""
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        mommy.make(InvalidatedUser, user=user, password_changed=False)
        login_ok = self.client.login(email=user.email, password="password")
        self.assertEqual(login_ok, True)
        self.assertEqual(InvalidatedUser.objects.count(), 1)
        self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=False).count(), 0)
        self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=True).count(), 1)

    def test_post_login_error_invalidated(self):
        """Test what happen when user with invalidated login try to login"""
        user = self._make(User, is_active=True, password="abd134", email="toto@toto.fr", username="toto")
        mommy.make(InvalidatedUser, user=user, password_changed=False)

        url = reverse('login')

        response = self.client.post(url, dict(email=user.email, password="password"))
        self.assertEqual(response.status_code, 200)

        form = self._get_from_context(response, 'form')
        self.assertNotEqual(form, None)
        self.assertEqual(form.invalidated_password, True)

        self.assertEqual(is_anonymous(self._get_user_from_context(response)), True)

        self.assertEqual(InvalidatedUser.objects.count(), 1)
        self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=False).count(), 1)

    def _get_from_context(self, response, var_name):
        """extract variable from context"""
        for context in response.context:
            if var_name in context:
                return context[var_name]

    def _get_user_from_context(self, response):
        """extract variable from context"""
        user = self._get_from_context(response, 'user')
        if user and user.is_authenticated:
            return User.objects.get(id=user.id)
        return user

    def test_post_login_error_not_invalidated(self):
        """Test what happen when user without invalidated login try to login"""
        user = self._make(User, is_active=True, password="abd134", email="toto@toto.fr", username="toto")

        url = reverse('login')

        response = self.client.post(url, dict(email=user.email, password="password"))
        self.assertEqual(response.status_code, 200)

        form = self._get_from_context(response, 'form')
        self.assertNotEqual(form, None)
        self.assertEqual(form.invalidated_password, False)

        self.assertEqual(is_anonymous(self._get_user_from_context(response)), True)

        self.assertEqual(InvalidatedUser.objects.count(), 0)

    def test_post_login_invalidated(self):
        """Test what happen when user with invalidated login, login"""
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")
        mommy.make(InvalidatedUser, user=user, password_changed=False)

        url = reverse('login')

        response = self.client.post(url, dict(email=user.email, password="password"), follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self._get_user_from_context(response), user)

        self.assertEqual(InvalidatedUser.objects.count(), 1)
        self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=False).count(), 0)
        self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=True).count(), 1)

    def test_post_login_not_invalidated(self):
        """Test what happen when user login"""
        user = self._make(User, is_active=True, password="password", email="toto@toto.fr", username="toto")

        url = reverse('login')

        response = self.client.post(url, dict(email=user.email, password="password"), follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self._get_user_from_context(response), user)

        self.assertEqual(InvalidatedUser.objects.count(), 0)

    def test_create_article_commands(self):
        user1 = self._make(User, is_active=True, password="password", email="toto1@toto.fr", username="toto1")
        user2 = self._make(User, is_active=True, password="password", email="toto2@toto.fr", username="toto2")

        self.assertEqual(InvalidatedUser.objects.count(), 0)

        management.call_command('invalidate_passwords', verbosity=0)

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(InvalidatedUser.objects.count(), 2)
        for user_id in (user1.id, user2.id):
            user = User.objects.get(id=user_id)
            self.assertEqual(InvalidatedUser.objects.filter(user=user).count(), 1)
            self.assertEqual(InvalidatedUser.objects.filter(user=user, password_changed=False).count(), 1)
            self.assertEqual(user.check_password("password"), False)
