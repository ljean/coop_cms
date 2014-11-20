# -*- coding: utf-8 -*-
"""This can be added to default context"""

from django.conf import settings


def cms_settings(request):
    """add jquey version to context"""
    context = {}

    if hasattr(settings, 'COOP_CMS_JQUERY_VERSION'):
        context['COOP_CMS_JQUERY_VERSION'] = settings.COOP_CMS_JQUERY_VERSION
    
    return context
