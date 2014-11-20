# -*- coding: utf-8 -*-
"""login form with Email rather than Username"""

from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext as _, ugettext_lazy as __


class EmailAuthForm(forms.Form):
    """Email form"""
    email = forms.EmailField(required=True, label=__(u"Email"))
    password = forms.CharField(label=__("Password"), widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.user_cache = None
        super(EmailAuthForm, self).__init__(*args, **kwargs)

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
                raise forms.ValidationError(
                    error_messages['invalid_login'],
                    code='invalid_login',
                    params={'email': _(u"email")},
                )

    def get_user(self):
        """return the user"""
        return self.user_cache

    def clean(self):
        """clean data"""
        self._authenticate()
        return self.cleaned_data
