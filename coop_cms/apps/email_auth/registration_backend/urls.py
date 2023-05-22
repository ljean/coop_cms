# -*- coding: utf-8 -*-

from django.urls import path
from django.views.generic.base import TemplateView

from .views import EmailRegistrationView, EmailActivationView

urlpatterns = [
    path(
        'activate/complete/',
        TemplateView.as_view(template_name='django_registration/activation_complete.html'),
        name='django_registration_activation_complete'
    ),
    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
    # that way it can return a sensible "invalid key" message instead of a
    # confusing 404.
    path(
        'activate/<str:activation_key>/',
        EmailActivationView.as_view(),
        name='registration_activate'
    ),
    path(
        'register/',
        EmailRegistrationView.as_view(),
        name='registration_register'
    ),
    path(
        'register/complete/',
        TemplateView.as_view(template_name='django_registration/registration_complete.html'),
        name='django_registration_complete'
    ),
    path(
        'register/closed/',
        TemplateView.as_view(template_name='django_registration/registration_closed.html'),
        name='django_registration_disallowed'
    ),
]
