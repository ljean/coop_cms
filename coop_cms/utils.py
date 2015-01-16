# -*- coding: utf-8 -*-
"""utils"""

from bs4 import BeautifulSoup
from HTMLParser import HTMLParser
from re import sub
from sys import stderr
from threading import current_thread
from traceback import print_exc

from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
from django.utils import translation

from coop_cms.settings import get_newsletter_context_callbacks


class _DeHTMLParser(HTMLParser):
    """html to text parser"""
    def __init__(self, allow_spaces=False):
        HTMLParser.__init__(self)
        self.__text = []
        self._allow_spaces = allow_spaces

    def handle_data(self, data):
        """parser"""
        text = data.strip()
        if len(text) > 0:
            if not self._allow_spaces:
                text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        """parser"""
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        """parser"""
        if tag == 'br':
            self.__text.append('\n\n')

    def text(self):
        """parser"""
        return ''.join(self.__text).strip()


# copied from http://stackoverflow.com/a/3987802/117092
def dehtml(text, allow_spaces=False):
    """html to text"""
    try:
        parser = _DeHTMLParser(allow_spaces=allow_spaces)
        parser.feed(text)
        parser.close()
        return parser.text()
    except Exception:
        print_exc(file=stderr)
        return text


def make_links_absolute(html_content, newsletter=None, site_prefix=""):
    """replace all local url with site_prefixed url"""
    
    def make_abs(url):
        if url.startswith('..'):
            url = url[2:]
        while url.startswith('/..'):
            url = url[3:]
        if url.startswith('/'):
            url = '%s%s' % (site_prefix, url)
        return url

    if not site_prefix:
        site_prefix = newsletter.get_site_prefix() if newsletter else settings.COOP_CMS_SITE_PREFIX

    soup = BeautifulSoup(html_content)
    for a_tag in soup.find_all("a"):
        if a_tag.get("href", None):
            a_tag["href"] = make_abs(a_tag["href"])
    
    for img_tag in soup.find_all("img"):
        if img_tag.get("src", None):
            img_tag["src"] = make_abs(img_tag["src"])
    
    return soup.prettify()
        

def send_newsletter(newsletter, dests, list_unsubscribe=None):
    """
    send newsletter
    newsletter : a newsletter object
    dests : the list of recipients
    list_unsubscribe : a list of url for unsubscribe
    """

    #Force the newsletter as public
    newsletter.is_public = True
    newsletter.save()

    lang = translation.get_language()[:2]
    if not (lang in [c for (c, n) in settings.LANGUAGES]):
        # The current language is not defined in sttings.LANGUAGE
        #force it to the defined language
        lang = settings.LANGUAGE_CODE[:2]
        translation.activate(lang)
    
    template = get_template(newsletter.get_template_name())
    context_dict = {
        'title': newsletter.subject, 'newsletter': newsletter, 'by_email': True,
        'SITE_PREFIX': settings.COOP_CMS_SITE_PREFIX,
        'MEDIA_URL': settings.MEDIA_URL, 'STATIC_URL': settings.STATIC_URL,
    }
    
    for callback in get_newsletter_context_callbacks():
        data = callback(newsletter)
        if data:
            context_dict.update(data)

    html_text = template.render(Context(context_dict))
    html_text = make_links_absolute(html_text, newsletter)
    
    emails = []
    connection = get_connection()
    from_email = settings.COOP_CMS_FROM_EMAIL
    reply_to = getattr(settings, 'COOP_CMS_REPLY_TO', None)
    headers = {}
    if reply_to:
        headers['Reply-To'] = reply_to
    if list_unsubscribe:
        headers['List-Unsubscribe'] = ", ".join(["<{0}>".format(url) for url in list_unsubscribe])

    for address in dests:
        text = dehtml(html_text)
        email = EmailMultiAlternatives(newsletter.subject, text, from_email, [address], headers=headers)
        email.attach_alternative(html_text, "text/html")
        emails.append(email)
    return connection.send_messages(emails)


class RequestNotFound(Exception):
    """exception"""
    pass


class RequestManager(object):
    """get django request from anywhere"""
    _shared = {}
    def __init__(self):
        """his is a Borg"""
        self.__dict__ = RequestManager._shared
        
    def _get_request_dict(self):
        """request dict"""
        if not hasattr(self, '_request'):
            self._request = {}
        return self._request
    
    def clean(self):
        """clean"""
        if hasattr(self, '_request'):
            del self._request
        
    def get_request(self):
        """return request"""
        _requests = self._get_request_dict()
        t = current_thread()
        if t not in _requests:
             raise RequestNotFound("Request not found: make sure that middleware is installed")
        return _requests[t]
    
    def set_request(self, request):
        """set request"""
        _requests = self._get_request_dict()
        _requests[current_thread()] = request


class RequestMiddleware(object):
    """middleware for request"""
    def process_request(self, request):
        RequestManager().set_request(request)
