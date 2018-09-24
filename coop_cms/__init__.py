# -*- coding: utf-8 -*-
"""
coop_cms is a Content Management System for Django
"""

from __future__ import unicode_literals


VERSION = (1, 3, 3)


def get_version():
    """returns version number"""
    version = '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])
    return version


__version__ = get_version()


default_app_config = 'coop_cms.apps.CoopCmsAppConfig'
