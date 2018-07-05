# -*- coding: utf-8 -*-
"""utils"""

from __future__ import unicode_literals

from re import sub
from sys import stderr
from traceback import print_exc

from django.utils.text import slugify as ascii_slugify
from slugify import slugify as unicode_slugify

from coop_cms.moves import HTMLParser
from coop_cms.settings import get_eastern_languages

from .i18n import get_language


class _DeHTMLParser(HTMLParser):
    """html to text parser"""
    def __init__(self, allow_spaces=False, allow_html_chars=False):
        HTMLParser.__init__(self)
        self._text = []
        self._allow_spaces = allow_spaces
        self._allow_html_chars = allow_html_chars

    def handle_data(self, data):
        """parser"""
        text = data
        if not self._allow_spaces:
            text = sub('[ \t\r\n]+', ' ', text)
        self._text.append(text)

    def handle_entityref(self, name):
        html_char = '&' + name + ";"
        if self._allow_html_chars:
            value = html_char
        else:
            value = self.unescape(html_char).replace('\xa0', ' ')
        self._text.append(value)

    def handle_charref(self, name):
        self.handle_entityref("#" + name)

    def handle_starttag(self, tag, attrs):
        """parser"""
        if tag == 'p':
            self._text.append('\n\n')
        elif tag == 'br':
            self._text.append('\n')

    def handle_startendtag(self, tag, attrs):
        """parser"""
        if tag == 'br':
            self._text.append('\n\n')

    def text(self):
        """parser"""
        return ''.join(self._text).strip()


def dehtml(text, allow_spaces=False, allow_html_chars=False):
    """
    html to text
    copied from http://stackoverflow.com/a/3987802/117092
    """
    try:
        parser = _DeHTMLParser(allow_spaces=allow_spaces, allow_html_chars=allow_html_chars)
        parser.feed(text)
        parser.close()
        return parser.text()
    except Exception:  # pylint: disable=broad-except
        print_exc(file=stderr)
        return text


def slugify(text, lang=None):
    """
    slugify a text. Use different method according to language
    "Here COmme the Sun" --> "here-come-the-sun"
    "Voici l'été" --> "voici-l-ete"
    "Миниаль бом" --> "Миниаль-бом"
    Args:
        text: a text to turn into a slug
        lang: the language of this text
    Returns: a slug
    """
    if lang is None:
        lang = get_language()

    if lang in get_eastern_languages():
        return unicode_slugify(text)
    else:
        return ascii_slugify(text)
