# -*- coding: utf-8 -*-
"""login form with Email rather than Username"""

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import ugettext as _, ugettext_lazy as __

from coop_cms.bs_forms import Form, BootstrapableMixin

from .models import InvalidatedUser


class EmailAuthForm(Form):
    """Email form"""
    invalidated_password = False

    email = forms.EmailField(required=True, label=__("Email"))
    password = forms.CharField(label=__("Password"), widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.user_cache = None
        super(EmailAuthForm, self).__init__(*args, **kwargs)

        if request:
            # Redirect to the next url after login
            if REDIRECT_FIELD_NAME in request.GET:
                self.fields[REDIRECT_FIELD_NAME] = forms.CharField(
                    initial=request.GET[REDIRECT_FIELD_NAME],
                    widget=forms.HiddenInput()
                )
            elif REDIRECT_FIELD_NAME in request.POST:
                # redirect to next even after error on the initial login form
                self.fields[REDIRECT_FIELD_NAME] = forms.CharField(
                    widget=forms.HiddenInput()
                )

    def _authenticate(self):
        """check authentication"""
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        error_messages = {
            'invalid_login': _("Please enter a correct %(email)s and password. "
                               "Note that both fields may be case-sensitive."),
        }

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if self.user_cache is None:

                # If we detect that the password may have been invalidated
                if InvalidatedUser.objects.filter(user__email=email, password_changed=False).exists():
                    self.invalidated_password = True

                raise forms.ValidationError(
                    error_messages['invalid_login'],
                    code='invalid_login',
                    params={'email': _("email")},
                )

    def get_user(self):
        """return the user"""
        return self.user_cache

    def clean(self):
        """clean data"""
        self._authenticate()
        return self.cleaned_data


class BsPasswordResetForm(BootstrapableMixin, PasswordResetForm):
    """Password reset form : Inherit from django_auth standard form. Add bootstrap style to fields"""
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()


class BsPasswordChangeForm(BootstrapableMixin, PasswordChangeForm):
    """Password change form : Inherit from django_auth standard form. Add bootstrap style to fields"""

    def __init__(self, *args, **kwargs):
        super(BsPasswordChangeForm, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()


class BsSetPasswordForm(BootstrapableMixin, SetPasswordForm):
    """Password set form : Inherit from django_auth standard form. Add bootstrap style to fields"""

    def __init__(self, *args, **kwargs):
        super(BsSetPasswordForm, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()
