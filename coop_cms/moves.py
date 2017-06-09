# -*- coding: utf-8 -*-
"""
coop_cms manage compatibilty with django and python versions
"""

import sys


from django import VERSION

if sys.version_info[0] < 3:
    # Python 2
    from HTMLParser import HTMLParser
    from StringIO import StringIO
else:
    # Python 3
    from html.parser import HTMLParser
    from io import BytesIO as StringIO


try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


if VERSION >= (1, 9, 0):
    from wsgiref.util import FileWrapper
else:
    from django.core.servers.basehttp import FileWrapper


if VERSION >= (1, 8, 0):
    from unittest import SkipTest
else:
    # Deprecated in Django 1.9
    from django.utils.unittest import SkipTest