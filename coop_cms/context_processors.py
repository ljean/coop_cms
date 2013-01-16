# -*- coding: utf-8 -*-

from django.conf import settings

def cms_settings(request):
    context = {}
    
    if hasattr(settings, 'COOP_CMS_JQUERY_VERSION'):
        context['COOP_CMS_JQUERY_VERSION'] = settings.COOP_CMS_JQUERY_VERSION
    
    return context
    