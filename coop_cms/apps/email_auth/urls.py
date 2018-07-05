# -*- coding: utf-8 -*-
"""urls"""

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.views import login, password_change, password_reset, password_reset_confirm

from coop_cms.apps.email_auth.forms import BsPasswordChangeForm, BsPasswordResetForm, EmailAuthForm, BsSetPasswordForm


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
    url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        {'set_password_form': BsSetPasswordForm},
        name='password_reset_confirm'
    ),
    url(r'^', include('django.contrib.auth.urls')),
]
