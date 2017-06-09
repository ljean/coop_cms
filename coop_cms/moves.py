# -*- coding: utf-8 -*-
"""
coop_cms manage compatibilty with django and python versions
"""

import sys


from django import VERSION

if sys.version_info[0] < 3:
    # Python 2

    from StringIO import StringIO

    from HTMLParser import HTMLParser



else:
    # Python 3
    from io import BytesIO as StringIO

    from html.parser import HTMLParser  as BaseHTMLParser

    class HTMLParser(BaseHTMLParser):
        def __init__(self):
            BaseHTMLParser.__init__(self, convert_charrefs=False)


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


def make_context(request, context_dict):
    """"""
    if VERSION >= (1, 9, 0):
        context = dict(context_dict)
        if request:
            context['request'] = request
    else:
        from django.template import RequestContext, Context
        if request:
            context = RequestContext(request, context_dict)
        else:
            context = Context(context_dict)
    return context
