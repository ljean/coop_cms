# -*- coding: utf-8 -*-
"""
coop_cms is a Content Management System for Django
"""
try:
    from django.core.exceptions import ImproperlyConfigured
    from django.conf import settings
    try:
        if 'localeurl' in settings.INSTALLED_APPS:
            from localeurl.models import patch_reverse
            patch_reverse()
    except ImproperlyConfigured:
        pass
except ImportError:
    pass

VERSION = (1, 0, 10)


def get_version():
    """returns version number"""
    version = '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])
    return version

__version__ = get_version()
