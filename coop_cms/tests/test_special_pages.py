# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from bs4 import BeautifulSoup
from unittest import skipIf


from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import REASON_NO_REFERER, REASON_NO_CSRF_COOKIE
from django.test.client import RequestFactory

from coop_cms.tests import BaseTestCase
from coop_cms.views import csrf_failure


@skipIf(getattr(settings, 'COOP_CMS_DO_NOT_INSTALL_CSRF_FAILURE_VIEW', False), "coo_cms csrf failure disabled")
class CsrfFailureTest(BaseTestCase):
    
    def test_view_reason_cookie(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        response = csrf_failure(request, REASON_NO_CSRF_COOKIE)
        
        self.assertEqual(403, response.status_code)
        soup = BeautifulSoup(response.content)
        
        self.assertEqual(1, len(soup.select('.cookies-error')))
        self.assertEqual(0, len(soup.select('.referer-error')))
        self.assertEqual(0, len(soup.select('.unknown-error')))
        
    
    def test_view_reason_referer(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        response = csrf_failure(request, REASON_NO_REFERER)
        
        self.assertEqual(403, response.status_code)
        soup = BeautifulSoup(response.content)
        
        self.assertEqual(0, len(soup.select('.cookies-error')))
        self.assertEqual(1, len(soup.select('.referer-error')))
        self.assertEqual(0, len(soup.select('.unknown-error')))
    
    def test_view_reason_unknown(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        response = csrf_failure(request, "?")
        
        self.assertEqual(403, response.status_code)
        soup = BeautifulSoup(response.content)
        
        self.assertEqual(0, len(soup.select('.cookies-error')))
        self.assertEqual(0, len(soup.select('.referer-error')))
        self.assertEqual(1, len(soup.select('.unknown-error')))
