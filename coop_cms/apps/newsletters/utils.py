# -*- coding: utf-8 -*-
"""utilities"""

from datetime import datetime
import re
import sys

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.mail import get_connection, EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import get_language as django_get_language, ugettext as _
from django.urls import reverse

from coop_cms.logger import logger
from coop_cms.models import Newsletter
from coop_cms.settings import get_newsletter_context_callbacks
from coop_cms.utils import dehtml, make_links_absolute

from .models import Emailing, MagicLink, Contact, Subscription, SubscriptionType


class EmailSendError(Exception):
    """An exception raise when sending email failed"""
    pass


def format_context(text, data):
    """replace custom templating by something compliant with python format function"""

    # { and } need to be escaped for the format function
    text = text.replace('{', '{{').replace('}', '}}')

    # #!- and -!# are turned into { and }
    text = text.replace('#!-', '{').replace('-!#', '}')

    return text.format(**data)


def get_emailing_context(emailing, contact):
    """get context for emailing: user,...."""
    data = dict(contact.__dict__)
    for field in ('fullname', ):
        data[field] = getattr(contact, field)
    
    # clone the object: Avoid overwriting {tags} for ever
    newsletter = Newsletter()
    newsletter.__dict__ = dict(emailing.newsletter.__dict__)

    newsletter.subject = format_context(newsletter.subject, data)

    html_content = format_context(newsletter.content, data)

    unregister_url = newsletter.get_site_prefix() + reverse('newsletters:unregister', args=[emailing.id, contact.uuid])
    
    newsletter.content = html_content

    context_dict = {
        'title': dehtml(newsletter.subject).replace('\n', ''),
        'newsletter': newsletter,
        'by_email': True,
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
        'SITE_PREFIX': emailing.get_domain_url_prefix(),
        'subscription_type_name': emailing.subscription_type.name,
        'unregister_url': unregister_url,
        'contact': contact,
        'emailing': emailing,
    }
    
    for callback in get_newsletter_context_callbacks():
        dictionary = callback(newsletter)
        if dictionary:
            context_dict.update(dictionary)
    
    return context_dict


def patch_emailing_html(html_text, emailing, contact):
    """transform links into magic link"""
    links = re.findall('href="(?P<url>.+?)"', html_text)

    ignore_links = [
        reverse("newsletters:unregister", args=[emailing.id, contact.uuid]),
        reverse("newsletters:view_online", args=[emailing.id, contact.uuid]),
    ]

    for lang_tuple in settings.LANGUAGES:
        lang = lang_tuple[0][:2]
        ignore_links.append(
            reverse("newsletters:view_online_lang", args=[emailing.id, contact.uuid, lang])
        )

    for link in links:
        if (not link.lower().startswith('mailto:')) and (link[0] != "#") and link not in ignore_links:
            # mailto, internal links, 'unregister' and 'view online' are not magic
            if len(link) < 500:

                magic_links = MagicLink.objects.filter(emailing=emailing, url=link)
                if magic_links.count() == 0:
                    magic_link = MagicLink.objects.create(emailing=emailing, url=link)
                else:
                    magic_link = magic_links[0]

                view_magic_link_url = reverse('newsletters:view_link', args=[magic_link.uuid, contact.uuid])
                magic_url = emailing.newsletter.get_site_prefix() + view_magic_link_url
                html_text = html_text.replace('href="{0}"'.format(link), 'href="{0}"'.format(magic_url))
            else:
                if 'test' not in sys.argv:
                    logger.warning(
                        "magic link size is greater than 500 ({0}) : {1}".format(len(link), link)
                    )
    return html_text


def send_newsletter(emailing, max_nb):
    """send newsletter"""

    # Clean the urls
    emailing.newsletter.content = make_links_absolute(
        emailing.newsletter.content, emailing.newsletter, site_prefix=emailing.get_domain_url_prefix()
    )
    
    connection = get_connection()
    from_email = emailing.subscription_type.from_email or settings.COOP_CMS_FROM_EMAIL
    emails = []
    
    contacts = list(emailing.send_to.all()[:max_nb])
    for contact in contacts:
        
        if contact.email:
            lang = emailing.lang or contact.favorite_language or settings.LANGUAGE_CODE[:2]
            translation.activate(lang)

            emailing_context = get_emailing_context(emailing, contact)
            emailing_context["LANGUAGE_CODE"] = lang
            context = emailing_context
            the_template = get_template(emailing.newsletter.get_template_name())

            html_text = the_template.render(context)

            html_text = patch_emailing_html(html_text, emailing, contact)

            html_text = make_links_absolute(
                html_text, emailing.newsletter, site_prefix=emailing.get_domain_url_prefix()
            )
            
            text = dehtml(html_text)
            list_unsubscribe_url = emailing.get_domain_url_prefix() + reverse(
                "newsletters:unregister", args=[emailing.id, contact.uuid]
            )
            list_unsubscribe_email = getattr(settings, 'COOP_CMS_REPLY_TO', '') or from_email
            headers = {
                "List-Unsubscribe": "<{0}>, <mailto:{1}?subject=unsubscribe>".format(
                    list_unsubscribe_url, list_unsubscribe_email
                )
            }

            if getattr(settings, 'COOP_CMS_REPLY_TO', None):
                headers['Reply-To'] = settings.COOP_CMS_REPLY_TO

            email = EmailMultiAlternatives(
                context['title'],
                force_line_max_length(text),
                from_email,
                [contact.email],
                headers=headers
            )
            html_text = force_line_max_length(html_text, max_length_per_line=400, dont_cut_in_quotes=True)
            email.attach_alternative(html_text, "text/html")
            emails.append(email)

        # print contact, "processed"
        emailing.send_to.remove(contact)
        emailing.sent_to.add(contact)
    
    emailing.save()
    nb_sent = connection.send_messages(emails)
    return nb_sent or 0


def on_bounce(event_type, email, description, permanent, contact_uuid, emailing_id):
    """can be called to signal soft or hard bounce"""
    contacts = Contact.objects.filter(email=email)

    # Unsubscribe emails for permanent errors
    if permanent:
        all_contacts = list(contacts)

        for contact in all_contacts:
            for subscription in contact.subscription_set.all():
                subscription.accept_subscription = False
                subscription.unsubscription_date = datetime.now()
                subscription.save()

    # Update emailing statistics
    if contact_uuid and emailing_id:
        try:
            contact = Contact.objects.get(uuid=contact_uuid)
        except Contact.DoesNotExist:
            contact = None

        try:
            emailing = Emailing.objects.get(id=emailing_id)
        except Emailing.DoesNotExist:
            emailing = None

        if contact and emailing and hasattr(emailing, event_type):
            getattr(emailing, event_type).add(contact)
            emailing.save()


def get_language():
    """wrap the django get_language and make sure: we return 2 chars"""
    lang = django_get_language()
    return lang[:2]


def force_line_max_length(text, max_length_per_line=400, dont_cut_in_quotes=True):
    """returns same text with end of lines inserted if lien length is greater than 400 chars"""
    out_text = ""
    for line in text.split("\n"):

        if len(line) < max_length_per_line:
            out_text += line + "\n"
        else:
            words = []
            line_length = 0
            quotes_count = 0
            for word in line.split(" "):
                if word:
                    words.append(word)
                    quotes_count += word.count('"')
                    line_length += len(word) + 1
                    in_quotes = (quotes_count % 2) == 1  # If there are not an even number we may be inside a ""
                    if line_length > max_length_per_line:
                        if not (not dont_cut_in_quotes and in_quotes):
                            # Line is more than allowed length for a line. Enter a end line character
                            out_line = " ".join(words)
                            out_text += out_line + "\n"
                            words = []
                            line_length = 0
            if words:
                out_line = " ".join(words)
                out_text += out_line + "\n"

    return out_text[:-1]  # Remove the last "\n"
