# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import ugettext as _

from registration.backends.model_activation.views import RegistrationView, ActivationView

from coop_cms.apps.email_auth.registration_backend.forms import RegistrationFormUniqueEmailAndTermsOfService


def notify_event(emails_to_notify, subject, template_name, extra_context):
    """notify an event to site managers"""
    if emails_to_notify:
        site = Site.objects.get_current()
        full_subject = "{0} - {1}".format(site, subject)
        the_template = get_template(template_name)
        context_dict = {'site': site}
        if extra_context:
            context_dict.update(extra_context)
        message = the_template.render(context_dict)
        send_mail(full_subject, message, settings.DEFAULT_FROM_EMAIL, list(emails_to_notify))


class EmailRegistrationView(RegistrationView):
    """register with email address"""
    form_class = RegistrationFormUniqueEmailAndTermsOfService

    def register(self, *args, **kwargs):
        new_user = super(EmailRegistrationView, self).register(*args, **kwargs)
        self.notify(new_user)
        return new_user

    def notify(self, new_user):
        """notify a list of people when a new account is creted"""
        emails_to_notify = getattr(settings, 'COOP_CMS_ACCOUNT_REGISTRATION_NOTIFICATION_EMAILS', None)
        notify_event(
            emails_to_notify,
            _("Account created"),
            'email_auth/registration_notification.txt',
            {'user': new_user, }
        )


class EmailActivationView(ActivationView):
    """activate account after user clicked on tokenized link"""

    def activate(self, *args, **kwargs):
        activated_user = super(EmailActivationView, self).activate(*args, **kwargs)
        self.notify(activated_user)
        return activated_user

    def notify(self, activated_user):
        """notify a list of people when a new account is activated"""
        emails_to_notify = getattr(settings, 'COOP_CMS_ACCOUNT_ACTION_NOTIFICATION_EMAILS', None)
        notify_event(
            emails_to_notify,
            _("Account activated"),
            'email_auth/activation_notification.txt',
            {'user': activated_user, }
        )
