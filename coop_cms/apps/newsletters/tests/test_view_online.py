# -*- coding: utf-8 -*-
"""test email sending"""

from unittest import skipIf

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse

from coop_cms.models import Newsletter
from coop_cms.settings import is_localized, is_multilang
from coop_cms.tests import BaseTestCase
from model_mommy import mommy

from .. import models


class ViewOnlineTest(BaseTestCase):

    def test_view_online(self):
        contact = mommy.make(models.Contact, email='toto@toto.fr')
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(models.Emailing, newsletter=newsletter)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:view_online', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, contact.fullname)
        self.assertEqual(models.MagicLink.objects.count(), 2)
        magic_link0 = models.MagicLink.objects.all()[0]
        self.assertContains(response, reverse('newsletters:view_link', args=[magic_link0.uuid, contact.uuid]))
        self.assertEqual(magic_link0.url, '/this-link-without-prefix-in-template')
        magic_link1 = models.MagicLink.objects.all()[1]
        self.assertContains(response, reverse('newsletters:view_link', args=[magic_link1.uuid, contact.uuid]))
        self.assertEqual(magic_link1.url, 'http://toto.fr')

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_emailing_view_online_lang(self):
        """test view emailing in other lang"""
        contact = mommy.make(models.Contact, email='toto@toto.fr')
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(models.Emailing, newsletter=newsletter)
        emailing.sent_to.add(contact)
        emailing.save()
        other_lang = settings.LANGUAGES[1][0]
        url = reverse('newsletters:view_online_lang', args=[emailing.id, contact.uuid, other_lang])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        next_url = reverse('newsletters:view_online', args=[emailing.id, contact.uuid])[3:]
        redirect_url = other_lang + next_url
        self.assertTrue(response['Location'].find(redirect_url) >= 0)

    @override_settings(SECRET_KEY="super-héros")
    def test_view_online_utf_links(self):
        contact = mommy.make(models.Contact, email='toto@toto.fr', first_name='Emmet', last_name='Brown')
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello #!-fullname-!#!</h2><p>Visit <a href="http://toto.fr/à-bientôt">à bientôt</a></p>',
            'template': 'test/newsletter_contact.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(models.Emailing, newsletter=newsletter)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:view_online', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, contact.fullname)
        self.assertEqual(models.MagicLink.objects.count(), 2)
        magic_link0 = models.MagicLink.objects.all()[0]
        self.assertContains(response, reverse('newsletters:view_link', args=[magic_link0.uuid, contact.uuid]))
        self.assertEqual(magic_link0.url, '/this-link-without-prefix-in-template')
        magic_link1 = models.MagicLink.objects.all()[1]
        self.assertContains(response, reverse('newsletters:view_link', args=[magic_link1.uuid, contact.uuid]))
        self.assertEqual(magic_link1.url, 'http://toto.fr/à-bientôt')

    def test_view_long_links(self):
        contact = mommy.make(models.Contact, email='toto@toto.fr', first_name='Emmet', last_name='Brown')
        short_link = "http://toto.fr/{0}".format("abcde" * 100)[:499]
        long_link = "http://toto.fr/{0}".format("abcde" * 100)  # >500 chars
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<p>Visit <a href="{0}">long link</a> <a href="{1}">long link</a></p>'.format(
                short_link, long_link
            ),
            'template': 'test/newsletter_no_link.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(models.Emailing, newsletter=newsletter)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:view_online', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(models.MagicLink.objects.count(), 1)
        magic_link0 = models.MagicLink.objects.all()[0]
        self.assertContains(response, reverse('newsletters:view_link', args=[magic_link0.uuid, contact.uuid]))
        self.assertEqual(magic_link0.url, short_link)
        self.assertContains(response, long_link)

    def test_view_duplicate_links(self):
        contact = mommy.make(models.Contact, email='toto@toto.fr', first_name='Emmet', last_name='Brown')
        short_link = "http://toto.fr/abcde/"
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<p>Visit <a href="{0}">link1</a> <a href="{1}">link2</a></p>'.format(
                short_link, short_link
            ),
            'template': 'test/newsletter_no_link.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing = mommy.make(models.Emailing, newsletter=newsletter)
        emailing.sent_to.add(contact)
        emailing.save()
        url = reverse('newsletters:view_online', args=[emailing.id, contact.uuid])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(models.MagicLink.objects.count(), 1)
        magic_link0 = models.MagicLink.objects.all()[0]
        self.assertContains(response, reverse('newsletters:view_link', args=[magic_link0.uuid, contact.uuid]))
        self.assertEqual(magic_link0.url, short_link)

    def test_view_duplicate_emailing(self):
        contact = mommy.make(models.Contact, email='toto@toto.fr', first_name='Emmet', last_name='Brown')
        short_link = "http://toto.fr/abcde/"
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<p>Visit <a href="{0}">link1</a></p>'.format(
                short_link
            ),
            'template': 'test/newsletter_no_link.html'
        }
        newsletter = mommy.make(Newsletter, **newsletter_data)
        emailing1 = mommy.make(models.Emailing, newsletter=newsletter)
        emailing1.sent_to.add(contact)
        emailing1.save()
        emailing2 = mommy.make(models.Emailing, newsletter=newsletter)
        emailing2.sent_to.add(contact)
        emailing2.save()
        for emailing in (emailing1, emailing2):
            url = reverse('newsletters:view_online', args=[emailing.id, contact.uuid])
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)
            magic_links = models.MagicLink.objects.filter(emailing=emailing)
            self.assertEqual(magic_links.count(), 1)
            magic_link0 = magic_links[0]
            self.assertContains(response, reverse('newsletters:view_link', args=[magic_link0.uuid, contact.uuid]))
            self.assertEqual(magic_link0.url, short_link)


