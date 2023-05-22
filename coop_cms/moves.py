# -*- coding: utf-8 -*-
"""
coop_cms manage compatibilty with django and python versions
"""

import json
import sys

from django.conf import settings
from django.template import RequestContext, Context

from html.parser import HTMLParser as BaseHTMLParser


class HTMLParser(BaseHTMLParser):
    def __init__(self):
        BaseHTMLParser.__init__(self, convert_charrefs=False)


try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


def make_context(request, context_dict, force_dict=True):
    """"""
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
    return context


def get_response_json(response):
    if sys.version_info[0] < 3:
        return json.loads(response.content)
    else:
        return response.json()


def is_authenticated(user):
    if callable(user.is_authenticated):
        return user.is_authenticated()
    return user.is_authenticated


def is_anonymous(user):
    return not is_authenticated(user)
