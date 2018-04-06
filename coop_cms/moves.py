# -*- coding: utf-8 -*-
"""
coop_cms manage compatibilty with django and python versions
"""

import json
import sys

from django import VERSION
from django.conf import settings
from django.template import RequestContext, Context


if sys.version_info[0] < 3:
    # Python 2
    from StringIO import StringIO
    from StringIO import StringIO as BytesIO
    from HTMLParser import HTMLParser
else:
    # Python 3
    from io import StringIO as StringIO
    from io import BytesIO as BytesIO
    from html.parser import HTMLParser as BaseHTMLParser

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


def make_context(request, context_dict, force_dict=True):
    """"""
    if VERSION >= (1, 9, 0):
        if force_dict:
            context = dict(context_dict)
            if request:
                context['request'] = request
                context['MEDIA_URL'] = settings.MEDIA_URL
                context['user'] = request.user
        else:
            if request:
                context = RequestContext(request, context_dict)
            else:
                context = Context(context_dict)
    else:
        if request:
            context = RequestContext(request, context_dict)
        else:
            context = Context(context_dict)
    return context


def get_response_json(response):
    if sys.version_info[0] < 3:
        return json.loads(response.content)
    else:
        return response.json()
