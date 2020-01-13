# -*- coding: utf-8 -*-
"""urls"""

from django.conf.urls import include, url
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView

from coop_cms.apps.email_auth.forms import BsPasswordChangeForm, BsPasswordResetForm, EmailAuthForm, BsSetPasswordForm


urlpatterns = [
    url(
        r'^login/$',
        LoginView.as_view(authentication_form=EmailAuthForm),
        name='login'
    ),
    url(r'^password_change/$',
        PasswordChangeView.as_view(form_class=BsPasswordChangeForm),
        name='password_change'
    ),
    url(
        r'^password_reset/$',
        PasswordResetView.as_view(form_class=BsPasswordResetForm),
        name='password_reset'
    ),
    url(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(form_class=BsSetPasswordForm),
        name='password_reset_confirm'
    ),
]
