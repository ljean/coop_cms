# -*- coding: utf-8 -*-
"""This can be added to default context"""

from django.conf import settings
from django.urls import reverse

from .models import get_homepage_url
from .settings import homepage_no_redirection


def cms_settings(request):
    """add jquery version to context"""
    context = {}

    if hasattr(settings, 'COOP_CMS_JQUERY_VERSION'):
        context['COOP_CMS_JQUERY_VERSION'] = settings.COOP_CMS_JQUERY_VERSION
    
    return context


def homepage_url(request):
    """add hoempage url to context"""
    context = {
        'homepage_url': reverse('coop_cms_homepage') if homepage_no_redirection() else get_homepage_url() ,
    }
    return context
