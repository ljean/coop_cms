# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.http import urlencode

from model_mommy import mommy

from colorbox.utils import assert_popup_redirects

from coop_cms.models import Link
from coop_cms.tests import BaseArticleTest, BeautifulSoup
from coop_cms.utils import get_login_url


class AddLinkTest(BaseArticleTest):

    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')

        ct = ContentType.objects.get_for_model(Link)

        perm = 'add_{0}'.format(ct.model)
        can_add_link = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add_link)

        user.is_active = True
        user.save()
        return self.client.login(username='toto', password='toto')

    def _log_as_non_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        user.save()
        return self.client.login(username='toto', password='toto')

    def test_view_new_link(self):
        url = reverse('coop_cms_new_link')
        self._log_as_editor()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(Link.objects.count(), 0)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("input#id_title")))
        self.assertEqual(1, len(soup.select("input#id_url")))
        self.assertEqual(1, len(soup.select("input#id_sites_0")))
        self.assertNotEqual(None, soup.select("input#id_sites_0")[0].get("checked", None))
        self.assertEqual(0, len(soup.select("input#id_sites_1")))

    def test_view_new_link_two_sites(self):
        mommy.make(Site)
        url = reverse('coop_cms_new_link')
        self._log_as_editor()
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(Link.objects.count(), 0)
        soup = BeautifulSoup(response.content)
        self.assertEqual(1, len(soup.select("input#id_title")))
        self.assertEqual(1, len(soup.select("input#id_url")))
        self.assertEqual(1, len(soup.select("input#id_sites_0")))
        self.assertEqual(1, len(soup.select("input#id_sites_1")))
        elt1 = soup.select("input#id_sites_0")[0]
        elt2 = soup.select("input#id_sites_1")[0]
        for elt in (elt1, elt2):
            # Only the current site is checked
            self.assertEqual('checked' in elt, elt["value"] == settings.SITE_ID)

    def test_view_new_link_non_editor(self):
        url = reverse('coop_cms_new_link')
        self._log_as_non_editor()
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)

    def test_view_new_link_anonymous(self):
        url = reverse('coop_cms_new_link')
        response = self.client.get(url, follow=True)
        auth_url = get_login_url()
        self.assertRedirects(response, auth_url + '?{0}'.format(urlencode({'next': url})))

    def test_add_link(self):
        self._log_as_editor()
        data = {'title': "test", 'url': "http://www.google.fr", 'sites': [settings.SITE_ID]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data)

        assert_popup_redirects(response, reverse('coop_cms_homepage'))

        self.assertEqual(Link.objects.count(), 1)
        link = Link.objects.all()[0]

        self.assertEqual(link.title, data['title'])
        self.assertEqual(link.url, data['url'])
        self.assertEqual(sorted([site.id for site in link.sites.all()]), [settings.SITE_ID])

    def test_add_link_internal(self):
        self._log_as_editor()
        data = {'title': "test", 'url': "/test", 'sites': [settings.SITE_ID]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data)

        assert_popup_redirects(response, reverse('coop_cms_homepage'))

        self.assertEqual(Link.objects.count(), 1)
        link = Link.objects.all()[0]

        self.assertEqual(link.title, data['title'])
        self.assertEqual(link.url, data['url'])
        self.assertEqual(sorted([site.id for site in link.sites.all()]), [settings.SITE_ID])

    def test_add_link_multi_sites(self):
        site2 = mommy.make(Site)
        mommy.make(Site)

        self._log_as_editor()
        data = {'title': "test", 'url': "http://www.google.fr", 'sites': [settings.SITE_ID, site2.id]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data)

        assert_popup_redirects(response, reverse('coop_cms_homepage'))

        self.assertEqual(Link.objects.count(), 1)
        link = Link.objects.all()[0]

        self.assertEqual(link.title, data['title'])
        self.assertEqual(link.url, data['url'])
        self.assertEqual(sorted([site.id for site in link.sites.all()]), [settings.SITE_ID, site2.id])

    def test_add_link_other_site(self):
        site2 = mommy.make(Site)

        self._log_as_editor()
        data = {'title': "test", 'url': "http://www.google.fr", 'sites': [site2.id]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data)

        assert_popup_redirects(response, reverse('coop_cms_homepage'))

        self.assertEqual(Link.objects.count(), 1)
        link = Link.objects.all()[0]

        self.assertEqual(link.title, data['title'])
        self.assertEqual(link.url, data['url'])
        self.assertEqual(sorted([site.id for site in link.sites.all()]), [site2.id])

    def test_add_link_no_site(self):
        site2 = mommy.make(Site)

        self._log_as_editor()
        data = {'title': "test", 'url': "http://www.google.fr", 'sites': []}

        response = self.client.post(reverse('coop_cms_new_link'), data=data)

        assert_popup_redirects(response, reverse('coop_cms_homepage'))

        self.assertEqual(Link.objects.count(), 1)
        link = Link.objects.all()[0]

        self.assertEqual(link.title, data['title'])
        self.assertEqual(link.url, data['url'])
        self.assertEqual(sorted([site.id for site in link.sites.all()]), [])

    def test_add_link_not_allowed(self):
        self._log_as_non_editor()
        data = {'title': "test", 'url': "http://www.google.fr", 'sites': [settings.SITE_ID]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data)

        self.assertEqual(response.status_code, 403)

        self.assertEqual(Link.objects.count(), 0)

    def test_add_link_anonymous(self):
        data = {'title': "test", 'url': "http://www.google.fr", 'sites': [settings.SITE_ID]}

        url = reverse('coop_cms_new_link')
        response = self.client.post(url, data=data, follow=True)

        auth_url = get_login_url()
        self.assertRedirects(response, auth_url + '?{0}'.format(urlencode({'next': url})))

        self.assertEqual(Link.objects.count(), 0)

    def test_add_link_no_url(self):

        self._log_as_editor()
        data = {'title': "test", 'url': "", 'sites': [settings.SITE_ID]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select("ul.errorlist")), 1)

        self.assertEqual(Link.objects.count(), 0)

    def test_add_link_no_title(self):
        self._log_as_editor()
        data = {'title': "", 'url': "http://www.google.fr", 'sites': [settings.SITE_ID]}

        response = self.client.post(reverse('coop_cms_new_link'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content)
        self.assertEqual(len(soup.select("ul.errorlist")), 1)

        self.assertEqual(Link.objects.count(), 0)
