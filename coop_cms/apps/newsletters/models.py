# -*- coding: utf-8 -*-
"""models"""

from datetime import datetime
import uuid

from django.conf import settings

from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from coop_cms.models import Newsletter


class Contact(models.Model):
    email = models.EmailField(verbose_name=_('email'), db_index=True)
    last_name = models.CharField(verbose_name=_('last name'), max_length=200, blank=True, default='')
    first_name = models.CharField(verbose_name=_('first name'), max_length=200, blank=True, default='')
    email_verified = models.BooleanField(_("email verified"), default=False)
    uuid = models.CharField(verbose_name=_('unique identifier'), max_length=200, blank=True, default='', db_index=True)
    favorite_language = models.CharField(_("favorite language"), max_length=10, default="", blank=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')

    @property
    def fullname(self):
        elements = [self.first_name, self.last_name]
        safe_elements = [elt for elt in elements if elt]
        return ' '.join(safe_elements)

    def save(self, *args, **kwargs):
        """save"""
        return_value = super().save(*args, **kwargs)
        if not self.uuid:
            name = '{0}-contact-{1}-{2}'.format(settings.SECRET_KEY, self.id, self.email)
            self.uuid = uuid.uuid5(uuid.NAMESPACE_URL, '{0}'.format(name))
            return super().save()
        return return_value


class SubscriptionType(models.Model):
    """Subscription type: a mailing list for example"""
    name = models.CharField(max_length=100, verbose_name=_("name"))
    site = models.ForeignKey(Site, blank=True, null=True, on_delete=models.CASCADE)
    order_index = models.IntegerField(default=0, verbose_name=_("order index"))
    allowed_on_sites = models.ManyToManyField(Site, blank=True, related_name='+')
    from_email = models.CharField(max_length=100, blank=True, default="", verbose_name=_("From email"))
    lang = models.CharField(_("language"), max_length=5, default="", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Subscription type')
        verbose_name_plural = _('Subscription types')
        ordering = ('order_index',)

    def get_domain_url_prefix(self):
        """domain url prefix"""
        if self.site:
            domain_protocol = getattr(settings, "COOP_CMS_DOMAIN_PROTOCOL", "http://")
            return domain_protocol + self.site.domain
        return ""


class Subscription(models.Model):
    """contact is subscribing to a mailing list"""
    subscription_type = models.ForeignKey(SubscriptionType, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)

    accept_subscription = models.BooleanField(
        _("accept subscription"), default=False,
        help_text=_('Keep this checked if you want to receive our newsletter.')
    )

    subscription_date = models.DateTimeField(blank=True, default=None, null=True)
    unsubscription_date = models.DateTimeField(blank=True, default=None, null=True)

    def __str__(self):
        return "{0} {1}".format(self.subscription_type, self.contact)


class Emailing(models.Model):
    """configuration on an emailing"""

    STATUS_EDITING = 1
    STATUS_SCHEDULED = 2
    STATUS_SENDING = 3
    STATUS_SENT = 4

    STATUS_CHOICES = (
        (STATUS_EDITING, _('Edition in progress')),
        (STATUS_SCHEDULED, _('Sending is scheduled')),
        (STATUS_SENDING, _('Sending in progress')),
        (STATUS_SENT, _('Sent')),
    )

    subscription_type = models.ForeignKey(SubscriptionType, on_delete=models.CASCADE)
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    send_to = models.ManyToManyField(Contact, blank=True, related_name="emailing_to_be_received")
    sent_to = models.ManyToManyField(Contact, blank=True, related_name="emailing_received")
    opened_emails = models.ManyToManyField(Contact, blank=True, related_name="emailing_opened")
    unsub = models.ManyToManyField(Contact, blank=True, related_name="emailing_unsub")
    status = models.IntegerField(default=STATUS_EDITING, choices=STATUS_CHOICES)

    creation_dt = models.DateTimeField(_(u"creation date"), blank=True, default=None, null=True)
    scheduling_dt = models.DateTimeField(_(u"scheduling date"), blank=True, default=None, null=True)
    sending_dt = models.DateTimeField(_(u"sending date"), blank=True, default=None, null=True)

    def __str__(self):
        return "{0} - {1} contacts".format(self.newsletter.subject, self.send_to.count())

    class Meta:
        verbose_name = _('emailing')
        verbose_name_plural = _('emailings')

    def save(self, *args, **kwargs):
        """save"""
        if self.creation_dt is None:
            self.creation_dt = datetime.now()

        if self.status == Emailing.STATUS_SENT and self.sending_dt is None:
            self.sending_dt = datetime.now()

        return super().save(*args, **kwargs)

    def get_domain_url_prefix(self):
        return self.subscription_type.get_domain_url_prefix()

    @property
    def from_email(self):
        return self.subscription_type.from_email

    @property
    def lang(self):
        return self.subscription_type.lang

    def get_absolute_url(self):
        if self.newsletter:
            return reverse('coop_cms_view_newsletter', args=[self.newsletter.id])



class MagicLink(models.Model):
    """A tracking link"""

    class Meta:
        verbose_name = _('Magic link')
        verbose_name_plural = _('Magic links')

    emailing = models.ForeignKey(Emailing, on_delete=models.CASCADE)
    url = models.URLField(max_length=500)
    visitors = models.ManyToManyField(Contact, blank=True)
    uuid = models.CharField(max_length=100, blank=True, default='', db_index=True)

    def __unicode__(self):
        return self.url

    def save(self, *args, **kwargs):
        """save"""
        return_value = super().save(*args, **kwargs)
        if not self.uuid:
            name = '{0}-magic-link-{1}-{2}'.format(settings.SECRET_KEY, self.id, self.url)
            self.uuid = uuid.uuid5(uuid.NAMESPACE_URL, name)
            return super().save()
        return return_value
