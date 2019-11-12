# -*- coding: utf-8 -*-
"""test email sending"""

from datetime import datetime
from unittest import skipIf

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import management
from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import activate

from coop_cms.models import Newsletter
from coop_cms.tests import BaseTestCase
from coop_cms.utils import get_url_in_language
from model_mommy import mommy

from .. import models


class SendEmailingTest(BaseTestCase):

    def setUp(self):
        activate(settings.LANGUAGES[0][0])
        super(SendEmailingTest, self).setUp()
        settings.COOP_CMS_FROM_EMAIL = 'toto@toto.fr'
        settings.COOP_CMS_REPLY_TO = 'titi@toto.fr'
        site = Site.objects.get_current()
        site.domain = settings.COOP_CMS_SITE_PREFIX
        site.save()

    def tearDown(self):
        activate(settings.LANGUAGES[0][0])

    @override_settings(COOP_CMS_REPLY_TO="")
    def test_send_newsletter(self):
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name + '@toto.fr')
            for name in names
        ]
        content = '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr">us</a>'
        content += '<a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a></p>'
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None,
            subscription_type=mommy.make(models.SubscriptionType, site=site)
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda _elt: _elt.to)
        contacts.sort(key=lambda _contact: _contact.email)
        for email, contact in zip(outbox, contacts):
            viewonline_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:view_online', args=[emailing.id, contact.uuid]
            )
            unsubscribe_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:unregister', args=[emailing.id, contact.uuid]
            )
            self.assertEqual(email.to, [contact.email])
            self.assertEqual(email.from_email, settings.COOP_CMS_FROM_EMAIL)
            self.assertEqual(email.subject, newsletter_data['subject'])
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertEqual(email.extra_headers.get('Reply-To', ''), '')
            self.assertEqual(
                email.extra_headers['List-Unsubscribe'],
                '<{0}>, <mailto:{1}?subject=unsubscribe>'.format(unsubscribe_url, email.from_email)
            )
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][0].find(viewonline_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(unsubscribe_url) >= 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("mailto:me@me.fr") > 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("#art1") > 0)
            # Check magic links
            self.assertTrue(models.MagicLink.objects.count() > 0)

    @skipIf(len(settings.LANGUAGES) < 2, "LANGUAGES less than 2")
    @override_settings(COOP_CMS_REPLY_TO="")
    def test_send_newsletter_language(self):
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(
                models.Contact,
                email=name+'@toto.fr',
                last_name=name.capitalize(),
                first_name=name,
            ) for name in names
        ]
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        content = '<h2>Hello #!-fullname-!#!</h2><p>{0}Visit <a href="http://toto.{0}">{0}</a>'
        content += '<a href="mailto:me@me.{0}">mailme</a><a href="#art1">internal link</a></p>'
        newsletter_data = {
            'subject_' + origin_lang: 'This is the {0} subject'.format(origin_lang),
            'subject_' + trans_lang: 'This is the {0} subject'.format(trans_lang),
            'content_' + origin_lang: content.format(origin_lang, ),
            'content_' + trans_lang: content.format(trans_lang),
            'template': 'test/newsletter_contact_lang.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None,
            subscription_type=mommy.make(models.SubscriptionType, site=site, lang=trans_lang),
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda _elt: _elt.to)
        contacts.sort(key=lambda _contact: _contact.email)
        activate(trans_lang)
        for email, contact in zip(outbox, contacts):
            viewonline_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:view_online', args=[emailing.id, contact.uuid]
            )
            unsubscribe_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:unregister', args=[emailing.id, contact.uuid]
            )
            view_en_url = reverse("newsletters:view_online_lang", args=[emailing.id, contact.uuid, 'en'])
            self.assertEqual(email.to, [contact.email])
            self.assertEqual(email.from_email, settings.COOP_CMS_FROM_EMAIL)
            self.assertEqual(email.subject, newsletter_data['subject_' + trans_lang])
            self.assertEqual(email.extra_headers.get('Reply-To', ''), '')
            self.assertEqual(
                email.extra_headers['List-Unsubscribe'],
                '<{0}>, <mailto:{1}?subject=unsubscribe>'.format(unsubscribe_url, email.from_email)
            )
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(contact.fullname) >= 0)
            # Check links are not magic
            self.assertTrue(email.alternatives[0][0].find(viewonline_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(unsubscribe_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(view_en_url) >= 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("mailto:me@me.{0}".format(trans_lang)) > 0)
            # Check internal links are not magic
            self.assertTrue(email.alternatives[0][0].find("#art1") > 0)
            # Check magic links
            self.assertTrue(models.MagicLink.objects.count() > 0)

    @skipIf(len(settings.LANGUAGES) < 2, "LANGUAGES less than 2")
    @override_settings(COOP_CMS_REPLY_TO="")
    def test_send_newsletter_contact_language(self):
        """test that we use the favorite language of the contact when sending him a newsletter"""
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        names = ['alpha', 'beta', 'gamma']
        langs = ['', origin_lang, trans_lang]
        contacts = [
            mommy.make(
                models.Contact,
                email=name+'@toto.fr',
                last_name=name.capitalize(),
                first_name=name,
                favorite_language=lang
            ) for (name, lang) in zip(names, langs)
        ]
        content = '<h2>Hello #!-fullname-!#!</h2><p>{0}Visit <a href="http://toto.{0}">{0}</a>'
        content += '<a href="mailto:me@me.{0}">mailme</a><a href="#art1">internal link</a></p>'
        newsletter_data = {
            'subject_' + origin_lang: 'This is the {0} subject'.format(origin_lang),
            'subject_' + trans_lang: 'This is the {0} subject'.format(trans_lang),
            'content_' + origin_lang: content.format(origin_lang),
            'content_' + trans_lang: content.format(trans_lang),
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None,
            subscription_type=mommy.make(models.SubscriptionType, site=site, lang=''),
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        activate(origin_lang)
        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda _elt: _elt.to)
        contacts.sort(key=lambda _contact: _contact.email)
        activate(trans_lang)
        for email, contact, lang in zip(outbox, contacts, langs):
            viewonline_url = reverse(
                'newsletters:view_online', args=[emailing.id, contact.uuid]
            )
            unsubscribe_url = reverse(
                'newsletters:unregister', args=[emailing.id, contact.uuid]
            )
            contact_lang = lang or origin_lang
            viewonline_url = get_url_in_language(viewonline_url, contact_lang)
            unsubscribe_url = get_url_in_language(unsubscribe_url, contact_lang)
            viewonline_url = emailing.get_domain_url_prefix() + viewonline_url
            unsubscribe_url = emailing.get_domain_url_prefix() + unsubscribe_url
            self.assertEqual(email.to, [contact.email])
            self.assertEqual(email.from_email, settings.COOP_CMS_FROM_EMAIL)
            self.assertEqual(email.subject, newsletter_data['subject_' + contact_lang])
            self.assertEqual(email.extra_headers.get('Reply-To', ''), '')
            self.assertEqual(
                email.extra_headers['List-Unsubscribe'],
                '<{0}>, <mailto:{1}?subject=unsubscribe>'.format(unsubscribe_url, email.from_email)
            )
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][0].find(viewonline_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(unsubscribe_url) >= 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("mailto:me@me.{0}".format(contact_lang)) > 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("#art1") > 0)
            # Check magic links
            self.assertTrue(models.MagicLink.objects.count() > 0)

    @override_settings(COOP_CMS_REPLY_TO="reply_to@toto.fr")
    def test_send_newsletter_reply_to(self):
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name+'@toto.fr', last_name=name.capitalize())
            for name in names
        ]
        content = '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr">us</a>'
        content += '<a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a></p>'
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None,
            subscription_type=mommy.make(models.SubscriptionType, site=site)
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda _elt: _elt.to)
        contacts.sort(key=lambda _contact: _contact.email)
        for email, contact in zip(outbox, contacts):
            viewonline_url = reverse(
                'newsletters:view_online', args=[emailing.id, contact.uuid]
            )
            unsubscribe_url = reverse(
                'newsletters:unregister', args=[emailing.id, contact.uuid]
            )
            viewonline_url = emailing.get_domain_url_prefix() + viewonline_url
            unsubscribe_url = emailing.get_domain_url_prefix() + unsubscribe_url

            self.assertEqual(email.to, [contact.email])
            self.assertEqual(email.from_email, settings.COOP_CMS_FROM_EMAIL)
            self.assertEqual(email.subject, newsletter_data['subject'])
            self.assertEqual(email.extra_headers['Reply-To'], settings.COOP_CMS_REPLY_TO)
            self.assertEqual(
                email.extra_headers['List-Unsubscribe'],
                '<{0}>, <mailto:{1}?subject=unsubscribe>'.format(unsubscribe_url, settings.COOP_CMS_REPLY_TO)
            )
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][0].find(viewonline_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(unsubscribe_url) >= 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("mailto:me@me.fr") > 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("#art1") > 0)
            # Check magic links
            self.assertTrue(models.MagicLink.objects.count() > 0)

    @override_settings(COOP_CMS_REPLY_TO="")
    def test_send_newsletter_from_email(self):
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name+'@toto.fr', last_name=name.capitalize())
            for name in names
        ]
        content = '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr">us</a>'
        content += '<a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a></p>'
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None,
            subscription_type=mommy.make(models.SubscriptionType, site=site, from_email="abcd@defg.fr"),
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda _elt: _elt.to)
        contacts.sort(key=lambda _contact: _contact.email)
        for email, contact in zip(outbox, contacts):
            viewonline_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:view_online', args=[emailing.id, contact.uuid]
            )
            unsubscribe_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:unregister', args=[emailing.id, contact.uuid]
            )
            self.assertEqual(email.to, [contact.email])
            self.assertEqual(email.from_email, emailing.from_email)
            self.assertEqual(email.subject, newsletter_data['subject'])
            self.assertEqual(
                email.extra_headers['List-Unsubscribe'],
                '<{0}>, <mailto:{1}?subject=unsubscribe>'.format(unsubscribe_url, emailing.from_email)
            )
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][0].find(viewonline_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(unsubscribe_url) >= 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("mailto:me@me.fr") > 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("#art1") > 0)
            # Check magic links
            self.assertTrue(models.MagicLink.objects.count() > 0)

    @override_settings(COOP_CMS_REPLY_TO="")
    def test_send_newsletter_check_unregister_name(self):
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name + '@toto.fr', last_name=name.capitalize())
            for name in names
        ]
        content = '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr">us</a>'
        content += '<a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a></p>'
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()
        subscription_1 = mommy.make(models.SubscriptionType, site=site, name="MY_COMPANY_#1")
        subscription_2 = mommy.make(models.SubscriptionType, site=site, name="MY_COMPANY_#2", from_email="abcd@defg.fr")
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None,
            subscription_type=subscription_2,
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda _elt: _elt.to)
        contacts.sort(key=lambda _contact: _contact.email)
        for email, contact in zip(outbox, contacts):
            viewonline_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:view_online', args=[emailing.id, contact.uuid]
            )
            unsubscribe_url = emailing.get_domain_url_prefix() + reverse(
                'newsletters:unregister', args=[emailing.id, contact.uuid]
            )
            self.assertFalse(email.body.find(subscription_1.name) >= 0)
            self.assertTrue(email.body.find(subscription_2.name) >= 0)
            self.assertEqual(email.to, [contact.email])
            self.assertEqual(email.from_email, emailing.from_email)
            self.assertEqual(email.subject, newsletter_data['subject'])
            self.assertEqual(
                email.extra_headers['List-Unsubscribe'],
                '<{0}>, <mailto:{1}?subject=unsubscribe>'.format(unsubscribe_url, emailing.from_email)
            )
            self.assertTrue(email.body.find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(contact.fullname) >= 0)
            self.assertTrue(email.alternatives[0][0].find(viewonline_url) >= 0)
            self.assertTrue(email.alternatives[0][0].find(unsubscribe_url) >= 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("mailto:me@me.fr") > 0)
            # Check mailto links are not magic
            self.assertTrue(email.alternatives[0][0].find("#art1") > 0)
            # Check magic links
            self.assertTrue(models.MagicLink.objects.count() > 0)
