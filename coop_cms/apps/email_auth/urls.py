# -*- coding: utf-8 -*-
"""urls"""

from django.conf.urls import include, url
from django.contrib.auth.views import login, password_change, password_reset

from coop_cms.apps.email_auth.forms import BsPasswordChangeForm, BsPasswordResetForm, EmailAuthForm


urlpatterns = [
    url(
        r'^login/$',
        login,
        {'authentication_form': EmailAuthForm},
        name='login'
    ),
    url(r'^password_change/$',
        password_change,
        {'password_change_form': BsPasswordChangeForm},
        name='password_change'
    ),
    url(
        r'^password_reset/$',
        password_reset,
        {'password_reset_form': BsPasswordResetForm},
        name='password_reset'
    ),
    url(r'^', include('django.contrib.auth.urls')),
]
