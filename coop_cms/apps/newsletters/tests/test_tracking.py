# -*- coding: utf-8 -*-
"""test email tracking"""

from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import management
from django.core import mail
from django.urls import reverse

from model_mommy import mommy
from coop_cms.models import Newsletter
from coop_cms.tests import BaseTestCase

from .. import models


class EmailTrackingTest(BaseTestCase):
    """Use a image to track opened emails"""

    def setUp(self):
        """before each test"""
        super(EmailTrackingTest, self).setUp()
        settings.COOP_CMS_FROM_EMAIL = 'toto@toto.fr'
        settings.COOP_CMS_REPLY_TO = 'titi@toto.fr'

        settings.COOP_CMS_SITE_PREFIX = "toto.fr"
        site = Site.objects.get_current()
        site.domain = "toto.fr"
        site.save()

    def test_track_image(self):
        """make sure that opened emails are incremented for every contact reading the email"""
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name+'@toto.fr')
            for name in names
        ]
        content = '''
            <h2>Hello #!-fullname-!#!</h2>
            <p>
            Visit <a href="http://toto.fr">us</a><a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a>
            </p>
        '''
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SENT,
            scheduling_dt=datetime.now(),
            sending_dt=datetime.now()
        )
        for contact in contacts:
            emailing.sent_to.add(contact)
        emailing.save()
        self.assertEqual(emailing.opened_emails.count(), 0)
        tracked_contacts = contacts[:-1]
        untracked_contacts = contacts[-1:]
        for contact in tracked_contacts:
            tracking_url = reverse("newsletters:email_tracking", args=[emailing.id, contact.uuid])
            response = self.client.get(tracking_url)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(emailing.opened_emails.count(), len(contacts)-1)
        for contact in tracked_contacts:
            self.assertTrue(contact in list(emailing.opened_emails.all()))
        for contact in untracked_contacts:
            self.assertFalse(contact in list(emailing.opened_emails.all()))

    def test_track_image_twice(self):
        """make sure that opened emails are not incremented twice for every contact reading the email"""
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name + '@toto.fr')
            for name in names
        ]
        content = '''
            <h2>Hello #!-fullname-!#!</h2>
            <p>
            Visit <a href="http://toto.fr">us</a><a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a>
            </p>
        '''
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SENT,
            scheduling_dt=datetime.now(),
            sending_dt=datetime.now()
        )
        for contact in contacts:
            emailing.sent_to.add(contact)
        emailing.save()
        self.assertEqual(emailing.opened_emails.count(), 0)
        self.assertEqual(emailing.opened_emails.count(), 0)
        tracked_contacts = contacts[:-1]
        untracked_contacts = contacts[-1:]
        for contact in tracked_contacts:
            tracking_url = reverse("newsletters:email_tracking", args=[emailing.id, contact.uuid])
            response = self.client.get(tracking_url)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(tracking_url)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(emailing.opened_emails.count(), len(contacts)-1)
        for contact in tracked_contacts:
            self.assertTrue(contact in list(emailing.opened_emails.all()))
        for contact in untracked_contacts:
            self.assertFalse(contact in list(emailing.opened_emails.all()))

    def test_send_newsletter_check_tracking(self):
        """make sure that tracking url is set in email"""
        names = ['alpha', 'beta', 'gamma']
        contacts = [
            mommy.make(models.Contact, email=name+'@toto.fr')
            for name in names
        ]
        content = '''
            <h2>Hello #!-fullname-!#!</h2>
            <p>
            Visit <a href="http://toto.fr">us</a><a href="mailto:me@me.fr">mailme</a><a href="#art1">internal link</a>
            </p>
        '''
        newsletter_data = {
            'subject': 'This is the subject',
            'content': content,
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(
            models.Emailing,
            newsletter=newsletter,
            status=models.Emailing.STATUS_SCHEDULED,
            scheduling_dt=datetime.now(),
            sending_dt=None
        )
        for contact in contacts:
            emailing.send_to.add(contact)
        emailing.save()
        management.call_command('send_newsletters', verbosity=0)
        emailing = models.Emailing.objects.get(id=emailing.id)
        # check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), len(contacts))
        self.assertEqual(len(mail.outbox), len(contacts))
        outbox = list(mail.outbox)
        outbox.sort(key=lambda elt: elt.to)
        contacts.sort(key=lambda contact: contact.email)
        for email, contact in zip(outbox, contacts):
            self.assertNotEqual(newsletter.get_site_prefix(), "")
            tracking_url = newsletter.get_site_prefix()
            tracking_url += reverse("newsletters:email_tracking", args=[emailing.id, contact.uuid])
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find(tracking_url) >= 0)
