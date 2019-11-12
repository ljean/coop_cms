# -*- coding: utf-8 -*-
"""test email sending"""

from django.conf import settings
from django.contrib.sites.models import Site

from coop_cms.tests.test_newsletter import NewsletterTest as BaseNewsletterTest


class NewsletterTest(BaseNewsletterTest):
    """test coop_cms newsletter"""

    def test_send_newsletter_template(self):
        def extra_checker(e):
            site = Site.objects.get(id=settings.SITE_ID)
            url = "http://"+site.domain+"/this-link-without-prefix-in-template"
            self.assertTrue(e.alternatives[0][0].find(url) >= 0)
        super(NewsletterTest, self).test_send_test_newsletter('test/newsletter_contact.html')
