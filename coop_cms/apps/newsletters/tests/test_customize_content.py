# -*- coding: utf-8 -*-
"""test email sending"""

from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import management
from django.core import mail

from coop_cms.models import Newsletter
from coop_cms.tests import BaseTestCase
from model_mommy import mommy

from .. import models


class CustomTemplateTest(BaseTestCase):
    """Test the user-templating"""

    def test_send_newsletter(self):
        contact = mommy.make(models.Contact, email='toto@toto.fr', first_name='Emmet', last_name='Brown')
        settings.COOP_CMS_FROM_EMAIL = 'toto@toto.fr'

        content = '''
        <h2>Hello #!-first_name-!# #!-last_name-!#</h2>
        Email: #!-email-!#
        '''

        newsletter_data = {
            'subject': 'Hello #!-first_name-!#',
            'content': content,
            'template': 'test/newsletter_contact.html',
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
            subscription_type=mommy.make(models.SubscriptionType, site=site),
        )

        emailing.send_to.add(contact)
        emailing.save()

        management.call_command('send_newsletters', verbosity=0)

        emailing = models.Emailing.objects.get(id=emailing.id)

        # Check emailing status
        self.assertEqual(emailing.status, models.Emailing.STATUS_SENT)
        self.assertNotEqual(emailing.sending_dt, None)
        self.assertEqual(emailing.send_to.count(), 0)
        self.assertEqual(emailing.sent_to.count(), 1)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.to, [contact.email])
        self.assertEqual(email.from_email, settings.COOP_CMS_FROM_EMAIL)

        self.assertTrue(email.alternatives[0][1], "text/html")

        html_body = email.alternatives[0][0]
        self.assertTrue(html_body.find(contact.fullname) >= 0)

        self.assertEqual(email.subject, 'Hello Emmet')

        fields = ('first_name', 'last_name', 'email',)
        for field_name in fields:
            self.assertTrue(email.body.find(getattr(contact, field_name)) >= 0)
            self.assertTrue(html_body.find(getattr(contact, field_name)) >= 0)
