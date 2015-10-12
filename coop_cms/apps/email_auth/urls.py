# -*- coding: utf-8 -*-
"""urls"""

from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, password_reset

from coop_cms.apps.email_auth.forms import EmailAuthForm, PasswordResetForm


urlpatterns = patterns('',
    url(r'^login/$', login, {'authentication_form': EmailAuthForm}, name='login'),
    url(r'^password/reset/$', password_reset, {'password_reset_form': PasswordResetForm}, name='password_reset'),
    (r'^', include('django.contrib.auth.urls')),
)
