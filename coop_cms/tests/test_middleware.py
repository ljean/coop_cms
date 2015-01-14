# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from django.test import TestCase

from coop_cms.utils import RequestManager, RequestMiddleware, RequestNotFound


class RequestManagerTest(TestCase):
    
    def test_get_request(self):
        r1 = {'user': "joe"}
        RequestMiddleware().process_request(r1)
        r2 = RequestManager().get_request()
        self.assertEqual(r1, r2)
        
    def test_get_request_no_middleware(self):
        RequestManager().clean()
        self.assertRaises(RequestNotFound, RequestManager().get_request)
