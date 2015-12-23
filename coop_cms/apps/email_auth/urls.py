# -*- coding: utf-8 -*-
"""urls"""

from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, password_change, password_reset

from coop_cms.apps.email_auth.forms import BsPasswordChangeForm, BsPasswordResetForm, EmailAuthForm


urlpatterns = patterns('',
    url(
        r'^login/$',
        'django.contrib.auth.views.login',
        {'authentication_form': EmailAuthForm},
        name=login
    ),
    url(r'^password_change/$',
        'django.contrib.auth.views.password_change',
        {'password_change_form': BsPasswordChangeForm},
        name=password_change
    ),
    url(
        r'^password_reset/$',
        'django.contrib.auth.views.password_reset',
        {'password_reset_form': BsPasswordResetForm},
        name=password_reset
    ),
    (r'^', include('django.contrib.auth.urls')),
)
