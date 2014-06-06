# -*- coding: utf-8 -*-

from HTMLParser import HTMLParser
from re import sub
from sys import stderr
from traceback import print_exc
from django.core.mail import get_connection, EmailMultiAlternatives
from coop_cms.html2text import html2text
from django.conf import settings
from django.template.loader import get_template
from django.template import Context
from coop_cms.settings import get_newsletter_context_callbacks
from bs4 import BeautifulSoup
from django.utils import translation


class _DeHTMLParser(HTMLParser):
    def __init__(self, allow_spaces=False):
        HTMLParser.__init__(self)
        self.__text = []
        self._allow_spaces = allow_spaces

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            if not self._allow_spaces:
                text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n\n')

    def text(self):
        return ''.join(self.__text).strip()


# copied from http://stackoverflow.com/a/3987802/117092
def dehtml(text, allow_spaces=False):
    try:
        parser = _DeHTMLParser(allow_spaces=allow_spaces)
        parser.feed(text)
        parser.close()
        return parser.text()
    except:
        print_exc(file=stderr)
        return text

def make_links_absolute(html_content, newsletter=None):
    """replace all local url with site_prefixed url"""
    
    def make_abs(url):
        if url.startswith('..'):
            url = url[2:]
        while url.startswith('/..'):
            url = url[3:]
        if url.startswith('/'):
            url = '%s%s' % (site_prefix, url)
        return url
    
    site_prefix = newsletter.get_site_prefix() if newsletter else settings.COOP_CMS_SITE_PREFIX
    soup = BeautifulSoup(html_content)
    for a_tag in soup.find_all("a"):
        if a_tag.get("href", None):
            a_tag["href"] = make_abs(a_tag["href"])
    
    for img_tag in soup.find_all("img"):
        if img_tag.get("src", None):
            img_tag["src"] = make_abs(img_tag["src"])
    
    return soup.prettify()
        
def send_newsletter(newsletter, dests):
    lang = translation.get_language()[:2]
    if not (lang in [c for (c, n) in settings.LANGUAGES]): # The current language is not defined in sttings.LANGUAGE
        #force it to the defined language
        lang = settings.LANGUAGE_CODE[:2]
        translation.activate(lang)
    
    t = get_template(newsletter.get_template_name())
    context_dict = {
        'title': newsletter.subject, 'newsletter': newsletter, 'by_email': True,
        'SITE_PREFIX': settings.COOP_CMS_SITE_PREFIX,
        'MEDIA_URL': settings.MEDIA_URL, 'STATIC_URL': settings.STATIC_URL,
    }
    
    for callback in get_newsletter_context_callbacks():
        d = callback(newsletter)
        if d:
            context_dict.update(d)

    html_text = t.render(Context(context_dict))
    html_text = make_links_absolute(html_text, newsletter)
    
    emails = []
    connection = get_connection()
    from_email = settings.COOP_CMS_FROM_EMAIL
    reply_to = getattr(settings, 'COOP_CMS_REPLY_TO', None)
    headers = {'Reply-To': reply_to} if reply_to else None

    for addr in dests:
        text = html2text(html_text)
        email = EmailMultiAlternatives(newsletter.subject, text, from_email, [addr], headers=headers)
        email.attach_alternative(html_text, "text/html")
        emails.append(email)
    return connection.send_messages(emails)
