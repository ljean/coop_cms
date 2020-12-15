# -*- coding: utf-8 -*-
"""utils"""

from bs4 import BeautifulSoup

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation

from coop_cms.settings import get_newsletter_context_callbacks, get_eastern_languages

from .text import dehtml
from .i18n import activate_lang, get_language


def strip_a_tags(pretty_html_text):
    """
    Reformat prettified html to remove spaces in <a> tags
    """
    pos = 0
    fixed_html = ''
    while True:
        new_pos = pretty_html_text.find('<a', pos)
        if new_pos > 0:
            fixed_html += pretty_html_text[pos:new_pos]
            end_tag = pretty_html_text.find('>', new_pos + 1)
            end_pos = pretty_html_text.find('</a>', end_tag + 1)

            fixed_html += pretty_html_text[new_pos:end_tag + 1]
            tag_content = pretty_html_text[end_tag + 1:end_pos]
            fixed_html += tag_content.strip() + '</a>'

            pos = end_pos + 4
        else:
            fixed_html += pretty_html_text[pos:]
            break

    return fixed_html


def _replace_from_end(s, a, b, times=None):
    """replace from end"""
    return s[::-1].replace(a, b, times)[::-1]


def avoid_line_too_long(pretty_html_text):
    """
    detect any line with more than 998 characters
    """
    lines = pretty_html_text.split('\n')
    new_lines = []
    for line in lines:
        line_length = len(line)
        if line_length >= 998:
            # Cut the line in several parts of 900 characters
            parts = []
            part_size = 900
            part_index = 0
            while part_size * len(parts) < line_length:
                parts.append(line[part_index*part_size:(part_index + 1)*part_size])
                part_index = len(parts)
            parts = [_replace_from_end(part, ' ', '\n', 1) for part in parts]
            new_lines.append(''.join(parts))
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)


def make_links_absolute(html_content, newsletter=None, site_prefix=""):
    """replace all local url with site_prefixed url"""
    
    def make_abs(url):
        """make absolute url"""
        if url.startswith('..'):
            url = url[2:]
        while url.startswith('/..'):
            url = url[3:]
        if url.startswith('/'):
            url = '%s%s' % (site_prefix, url)
        return url

    if not site_prefix:
        if newsletter:
            site_prefix = newsletter.get_site_prefix()
        else:
            site = Site.objects.get_current()
            site_prefix = "http://{0}".format(site.domain)

    soup = BeautifulSoup(html_content, 'html.parser')
    for a_tag in soup.find_all("a"):
        if a_tag.get("href", None):
            a_tag["href"] = make_abs(a_tag["href"])
    
    for img_tag in soup.find_all("img"):
        if img_tag.get("src", None):
            img_tag["src"] = make_abs(img_tag["src"])

    pretty_html = soup.prettify()
    fixed_html = strip_a_tags(pretty_html)
    return avoid_line_too_long(fixed_html)


def _send_email(subject, html_text, dests, list_unsubscribe):
    """send an email"""
    emails = []
    connection = get_connection()
    from_email = getattr(settings, 'COOP_CMS_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
    reply_to = getattr(settings, 'COOP_CMS_REPLY_TO', None)

    # make header
    headers = {}
    if reply_to:
        headers['Reply-To'] = reply_to
    if list_unsubscribe:
        headers['List-Unsubscribe'] = ", ".join(["<{0}>".format(url) for url in list_unsubscribe])

    for address in dests:
        text = dehtml(html_text)
        email = EmailMultiAlternatives(subject, text, from_email, [address], headers=headers)
        email.attach_alternative(html_text, "text/html")
        emails.append(email)
    return connection.send_messages(emails)


def send_email(subject, template_name, context, site_prefix, dests, lang=None, list_unsubscribe=None):
    """Send an HTML email"""
    activate_lang(lang)

    the_template = get_template(template_name)

    try:
        html_text = the_template.render(context)
    except Exception:
        # import traceback
        # print traceback.print_exc()
        raise

    html_text = make_links_absolute(html_text, site_prefix=site_prefix)

    return _send_email(subject, html_text, dests, list_unsubscribe=list_unsubscribe)


def send_newsletter(newsletter, dests, list_unsubscribe=None):
    """
    send newsletter
    newsletter : a newsletter object
    dests : the list of recipients
    list_unsubscribe : a list of url for unsubscribe
    """

    # Force the newsletter as public
    newsletter.is_public = True
    newsletter.save()

    lang = get_language()
    if not (lang in [code_and_name[0] for code_and_name in settings.LANGUAGES]):
        # The current language is not defined in settings.LANGUAGE
        # force it to the defined language
        lang = settings.LANGUAGE_CODE[:2]
        translation.activate(lang)

    the_template = get_template(newsletter.get_template_name())
    context_dict = {
        'title': newsletter.subject,
        'newsletter': newsletter,
        'by_email': True,
        'SITE_PREFIX': settings.COOP_CMS_SITE_PREFIX,
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
    }

    for callback in get_newsletter_context_callbacks():
        data = callback(newsletter)
        if data:
            context_dict.update(data)

    try:
        html_text = the_template.render(context_dict)
    except Exception:
        # import traceback
        # print(traceback.print_exc())
        raise

    html_text = make_links_absolute(html_text, newsletter)
    subject = ' '.join(newsletter.subject.split('\n'))
    subject = ' '.join(subject.split('\r'))

    return _send_email(subject, html_text, dests, list_unsubscribe)
