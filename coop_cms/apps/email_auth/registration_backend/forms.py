# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationFormUniqueEmail

from coop_cms.bs_forms import BootstrapableMixin


class RegistrationFormUniqueEmailAndTermsOfService(BootstrapableMixin, RegistrationFormUniqueEmail):
    
    terms_of_service = forms.BooleanField(
        widget=forms.CheckboxInput,
        label=_('I have read and agree to the Terms of Service'),
        error_messages={'required': _("You must agree to the terms to register")}
    )

    def __init__(self, *args, **kwargs):
        super(RegistrationFormUniqueEmailAndTermsOfService, self).__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['username'].widget = forms.HiddenInput()
        self._bs_patch_field_class()

    def clean(self):
        ret = super(RegistrationFormUniqueEmailAndTermsOfService, self).clean()
        email = self.cleaned_data.get('email', '')
        if email:
            self.cleaned_data['username'] = email[:30]
        return ret
