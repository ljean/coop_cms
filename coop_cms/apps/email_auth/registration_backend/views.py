# -*- coding: utf-8 -*-

from registration.backends.default.views import RegistrationView, ActivationView

from coop_cms.apps.email_auth.registration_backend.forms import RegistrationFormUniqueEmailAndTermsOfService


class EmailRegistrationView(RegistrationView):
    """register with email address"""
    form_class = RegistrationFormUniqueEmailAndTermsOfService


class EmailActivationView(ActivationView):
    pass