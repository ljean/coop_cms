# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

import logging
import os.path
import shutil

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from coop_cms.settings import get_article_class

try:
    AUTH_LOGIN_NAME = "auth_login"
    reverse(AUTH_LOGIN_NAME)
except:
    AUTH_LOGIN_NAME = "login"

def make_dt(dt):
    if settings.USE_TZ:
        return timezone.make_aware(dt, timezone.get_default_timezone())
    else:
        return dt

default_media_root = settings.MEDIA_ROOT


#Used by a test below
def dummy_image_width(img):
    return 20


@override_settings(MEDIA_ROOT=os.path.join(default_media_root, '_unit_tests'))
class BaseTestCase(TestCase):
    def _clean_files(self):
        if default_media_root != settings.MEDIA_ROOT:
            try:
                shutil.rmtree(settings.MEDIA_ROOT)
            except OSError:
                pass
        else:
            raise Exception("Warning! wrong media root for unittesting")
    
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self._clean_files()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        self._clean_files()

    
class MediaBaseTestCase(BaseTestCase):

    def _get_file(self, file_name='unittest1.txt'):
        full_name = os.path.normpath(os.path.dirname(__file__) + '/fixtures/' + file_name)
        return open(full_name, 'rb')

    def _log_as_mediamgr(self, is_staff=True, perm=None):
        u = User.objects.create(username='toto', is_staff=is_staff)
        u.set_password('toto')
        if perm:
            u.user_permissions.add(perm)
        u.save()
        logged = self.client.login(username='toto', password='toto')
        if not logged: raise Exception("Not logged")

    def _permission(self, code, model_class):
        ct = ContentType.objects.get_for_model(model_class)
        codename = '{0}_{1}'.format(code, ct.model)
        return Permission.objects.get(content_type__app_label=ct.app_label, codename=codename)


class UserBaseTestCase(BaseTestCase):

    def setUp(self):
        super(UserBaseTestCase, self).setUp()
        self.editor = None
        self.viewer = None

    def _log_as_editor(self, can_add=False):
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

            if can_add:
                codename = 'add_{0}'.format(ct.model)
                can_add_article = Permission.objects.get(content_type__app_label=ct.app_label, codename=codename)
                self.editor.user_permissions.add(can_add_article)

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



class BaseArticleTest(MediaBaseTestCase):
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

