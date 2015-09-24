# -*- coding: utf-8 -*-

from registration.backends.default.views import RegistrationView, ActivationView

from coop_cms.apps.email_auth.registration_backend.forms import RegistrationFormUniqueEmailAndTermsOfService


class EmailRegistrationView(RegistrationView):
    """register with email address"""
    form_class = RegistrationFormUniqueEmailAndTermsOfService

    def register(self, request, **cleaned_data):
        """new user register to the service"""
        cleaned_data['username'] = cleaned_data["email"][:30]
        return super(EmailRegistrationView, self).register(request, **cleaned_data)


class EmailActivationView(ActivationView):
    pass