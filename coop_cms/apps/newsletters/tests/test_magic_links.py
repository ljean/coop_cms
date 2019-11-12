# -*- coding: utf-8 -*-
"""test email sending"""

from django.urls import reverse

from coop_cms.tests.test_newsletter import BaseTestCase
from model_mommy import mommy

from .. import models


class MagicLinkTest(BaseTestCase):

    def test_view_magic_link(self):
        contact = mommy.make(models.Contact,email='toto@toto.fr', last_name='Toto')
        emailing = mommy.make(models.Emailing)
        emailing.sent_to.add(contact)
        emailing.save()
        link = "http://www.google.fr"
        magic_link = models.MagicLink.objects.create(emailing=emailing, url=link)
        self.assertEqual(magic_link.visitors.count(), 0)
        response = self.client.get(reverse('newsletters:view_link', args=[magic_link.uuid, contact.uuid]))
        self.assertEqual(302, response.status_code)
        self.assertEqual(response['Location'], link)
        self.assertEqual(magic_link.visitors.count(), 1)
        self.assertEqual(magic_link.visitors.all()[0], contact)
