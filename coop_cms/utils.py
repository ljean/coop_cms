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
from django.core.urlresolvers import reverse
from coop_cms.settings import get_article_class, is_localized, get_newsletter_context_callbacks
from coop_cms.models import BaseArticle, Alias
from django.utils.translation import get_language
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from bs4 import BeautifulSoup

class _DeHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
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
def dehtml(text):
    try:
        parser = _DeHTMLParser()
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
    
#def make_links_absolute(html_content, newsletter=None):
#    """replace all local url with absolute url"""
#    import re
#    #regex = """<.*(?P<tag>href|src)\s*=\s*["'](?P<url>.+?)["'].*>"""
#    #regex = """<.*href|src\s*=\s*["'](?P<url>.+?)["'].*>"""
#    
#    site_prefix = newsletter.get_site_prefix() if newsletter else settings.COOP_CMS_SITE_PREFIX
#    
#    def make_abs(match):
#        #Thank you : http://www.gawel.org/howtos/python-re-sub
#        start = match.group('start')
#        url = match.group('url')
#        
#        if url.startswith('..'):
#            url = url[2:]
#        while url.startswith('/..'):
#            url = url[3:]
#        if url.startswith('/'):
#            url = '%s%s' % (site_prefix, url)
#        end = match.group('end')
#        
#        print start, url, end
#        
#        return start + url + end
#    
#    #a_pattern = re.compile(ur'(?P<start>.*?href=")(?P<url>\S+)(?P<end>".*?)')
#    a_pattern = re.compile(r"""(?P<start>.*?href=")(?P<url>\S+)(?P<end>".*?)""")
#    html_content = a_pattern.sub(make_abs, html_content)
#    #raise
#    
#    img_pattern = re.compile(r'(?P<start>.*?src=")(?P<url>\S+)(?P<end>".*?)')
#    html_content = img_pattern.sub(make_abs, html_content)
#
#    return html_content
    
def send_newsletter(newsletter, dests):

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

def get_article_slug(*args, **kwargs):
    slug = reverse(*args, **kwargs)
    if 'localeurl' in settings.INSTALLED_APPS:
        #If localeurl is installed reverse is patched
        #We must remove the lang prefix
        from localeurl.utils import strip_path
        lang, slug = strip_path(slug)
    return slug.strip('/')

def get_article(slug, current_lang=None, force_lang=None, **kwargs):
    Article = get_article_class()
    try:
        return Article.objects.get(slug=slug, **kwargs)
    except Article.DoesNotExist:
        #if modeltranslation is installed,
        #if no article correspond to the current language article
        #try to look for slug in default language
        if is_localized():
            from modeltranslation import settings as mt_settings
            default_lang = mt_settings.DEFAULT_LANGUAGE
            lang = force_lang
            if not lang:
                current_lang = get_language()
                if current_lang != default_lang:
                    lang = default_lang
            if lang:
                kwargs.update({'slug_{0}'.format(lang): slug})
                return Article.objects.get(**kwargs)
        raise #re-raise previous error

def get_article_or_404(slug, **kwargs):
    Article = get_article_class()
    try:
        return get_article(slug, **kwargs)
    except Article.DoesNotExist:
        raise Http404

def get_headlines(article):
    Article = get_article_class()
    if article.is_homepage:
        return Article.objects.filter(headline=True, publication=BaseArticle.PUBLISHED).order_by("-publication_date")
    return Article.objects.none()
    
def redirect_if_alias(path):
    alias = get_object_or_404(Alias, path=path)
    if alias.redirect_url:
        return HttpResponsePermanentRedirect(alias.redirect_url)
    else:
        raise Http404