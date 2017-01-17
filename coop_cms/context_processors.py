# -*- coding: utf-8 -*-
"""This can be added to default context"""

from django.conf import settings
from coop_cms.utils import get_homepage_url

def cms_settings(request):
    """add jquery version to context"""
    context = {}

    if hasattr(settings, 'COOP_CMS_JQUERY_VERSION'):
        context['COOP_CMS_JQUERY_VERSION'] = settings.COOP_CMS_JQUERY_VERSION
    
    return context


def homepage_url(request):
    """add hoempage url to context"""
    context = {
        'homepage_url': get_homepage_url(),
    }
    return context
