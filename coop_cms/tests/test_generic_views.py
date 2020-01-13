# -*- coding: utf-8 -*-

from django.conf import settings

from coop_cms.moves import SkipTest

if 'coop_cms.apps.test_app' in settings.INSTALLED_APPS:
    from coop_cms.apps.test_app.tests import GenericViewTestCase as BaseGenericViewTestCase
else:
    from coop_cms.tests import BaseTestCase as BaseGenericViewTestCase


class GenericViewTestCase(BaseGenericViewTestCase):
    warning = """
    Add this to your settings.py to enable this test:
    if len(sys.argv)>1 and 'test' == sys.argv[1]:
        INSTALLED_APPS = INSTALLED_APPS + ('coop_cms.apps.test_app',)
    """
    
    def setUp(self):
        super(GenericViewTestCase, self).setUp()
        if not ('coop_cms.apps.test_app' in settings.INSTALLED_APPS):
            raise SkipTest('coop_cms.apps.test_app not installed')
