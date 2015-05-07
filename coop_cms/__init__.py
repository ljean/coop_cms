# -*- coding: utf-8 -*-
"""
coop_cms is a Content Management System for Django
"""

VERSION = (1, 0, 13)


def get_version():
    """returns version number"""
    version = '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])
    return version

__version__ = get_version()
