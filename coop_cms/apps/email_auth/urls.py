# -*- coding: utf-8 -*-
"""urls"""

from django.urls import path, re_path
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView

from .forms import BsPasswordChangeForm, BsPasswordResetForm, EmailAuthForm, BsSetPasswordForm


urlpatterns = [
    path(
        'login/',
        LoginView.as_view(authentication_form=EmailAuthForm),
        name='login'
    ),
    path('password_change/',
        PasswordChangeView.as_view(form_class=BsPasswordChangeForm),
        name='password_change'
    ),
    path(
        'password_reset/',
        PasswordResetView.as_view(form_class=BsPasswordResetForm),
        name='password_reset'
    ),
    re_path(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(form_class=BsSetPasswordForm),
        name='password_reset_confirm'
    ),
]
