# -*- coding: utf-8 -*-
"""urls"""

from django.conf.urls import patterns, include, url

from coop_cms.apps.email_auth.forms import EmailAuthForm


urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login', {'authentication_form': EmailAuthForm}, name='login'),
    (r'^', include('django.contrib.auth.urls')),
)
