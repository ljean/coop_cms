# -*- coding: utf-8 -*-
"""test email sending"""

from django.contrib.sites.models import Site
from django.urls import reverse

from coop_cms.tests import BaseTestCase
from model_mommy import mommy

from .. import models


class UnregisterTest(BaseTestCase):

    def test_unregister_mailinglist(self):
        site1 = Site.objects.get_current()
        newsletter_subscription = mommy.make(models.SubscriptionType, name="newsletter", site=site1)
        third_party_subscription = mommy.make(models.SubscriptionType, name="3rd_party", site=site1)
        contact = mommy.make(models.Contact, email='toto@toto.fr', last_name='Toto')
        subscription1 = mommy.make(
            models.Subscription,
            subscription_type=newsletter_subscription,
            contact=contact,
            accept_subscription=True
        )
        subscription2 = mommy.make(
            models.Subscription,
            subscription_type=third_party_subscription,
            contact=contact,
            accept_subscription=True
        )
        emailing = mommy.make(models.Emailing, subscription_type=newsletter_subscription)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:unregister', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        response = self.client.post(url, data={'unregister': True})
        self.assertEqual(200, response.status_code)
        subscription1 = models.Subscription.objects.get(id=subscription1.id)
        self.assertEqual(subscription1.accept_subscription, False)
        self.assertEqual(subscription1.contact, contact)
        subscription2 = models.Subscription.objects.get(id=subscription2.id)
        self.assertEqual(subscription2.accept_subscription, True)
        self.assertEqual(subscription2.contact, contact)
        self.assertEqual(emailing.unsub.count(), 1)
        self.assertEqual(emailing.unsub.all()[0], contact)

    def test_unregister_mailinglist_dont_exist(self):
        site1 = Site.objects.get_current()
        newsletter_subscription = mommy.make(models.SubscriptionType, name="newsletter", site=site1)
        contact = mommy.make(models.Contact, email='toto@toto.fr', last_name='Toto')
        emailing = mommy.make(models.Emailing, subscription_type=newsletter_subscription)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:unregister', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        response = self.client.post(url, data={'unregister': True})
        self.assertEqual(200, response.status_code)
        subscription1 = models.Subscription.objects.get(subscription_type=newsletter_subscription)
        self.assertEqual(subscription1.accept_subscription, False)
        self.assertEqual(subscription1.contact, contact)
        self.assertEqual(emailing.unsub.count(), 1)
        self.assertEqual(list(emailing.unsub.all()), [contact])

    def test_unregister_mailinglist_twice(self):
        site1 = Site.objects.get_current()
        newsletter_subscription = mommy.make(models.SubscriptionType, name="newsletter", site=site1)
        contact = mommy.make(models.Contact, email='toto@toto.fr', last_name='Toto')
        subscription1 = mommy.make(
            models.Subscription,
            subscription_type=newsletter_subscription,
            contact=contact,
            accept_subscription=False
        )
        emailing = mommy.make(models.Emailing, subscription_type=newsletter_subscription)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:unregister', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        response = self.client.post(url, data={'unregister': True})
        self.assertEqual(200, response.status_code)
        subscription1 = models.Subscription.objects.get(id=subscription1.id)
        self.assertEqual(subscription1.accept_subscription, False)
        self.assertEqual(subscription1.contact, contact)
        self.assertEqual(emailing.unsub.count(), 1)
        self.assertEqual(list(emailing.unsub.all()), [contact])

    def test_unregister_mailinglist_notfound_emailing(self):
        site1 = Site.objects.get_current()
        contact = mommy.make(models.Contact, email='toto@toto.fr')
        url = reverse('newsletters:unregister', args=[1, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)
        response = self.client.post(url, data={'unregister': True})
        self.assertEqual(404, response.status_code)
        self.assertEqual(models.Emailing.objects.count(), 0)

    def test_unregister_mailinglist_not_found_contact(self):
        site1 = Site.objects.get_current()
        newsletter_subscription = mommy.make(models.SubscriptionType, name="newsletter", site=site1)
        emailing = mommy.make(models.Emailing, subscription_type=newsletter_subscription)
        url = reverse('newsletters:unregister', args=[emailing.id, "aaaa"])
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)
        response = self.client.post(url, data={'unregister': True})
        self.assertEqual(404, response.status_code)
        self.assertEqual(emailing.unsub.count(), 0)
