# -*- coding: utf-8 -*-
"""utils"""

from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.utils import translation


def activate_lang(lang=None):
    lang = lang or get_language()
    language_codes = [code_and_name[0] for code_and_name in settings.LANGUAGES]
    if not (lang in language_codes):
        # The current language is not defined in settings.LANGUAGE
        # force it to the defined language
        lang = settings.LANGUAGE_CODE[:2]
    translation.activate(lang)


def get_language():
    """returns the language or default language"""
    lang = translation.get_language()
    if lang:
        return lang[:2]
    else:
        return settings.LANGUAGE_CODE[:2]


def get_url_in_language(url, lang_code):
    """returns the url in another language"""
    if lang_code and translation.check_for_language(lang_code):
        path = strip_locale_path(url)[1]
        new_url = make_locale_path(path, lang_code)
        return new_url
    else:
        raise ImproperlyConfigured("{0} is not a valid language".format(lang_code))


def strip_locale_path(locale_path):
    """returns language independent url - /en/home/ --> /home/"""
    elements = locale_path.split('/')
    if len(elements) > 2:
        lang = elements[1]
        if lang in [lang_and_name[0] for lang_and_name in settings.LANGUAGES]:
            del elements[1]
            return lang, '/'.join(elements)
    return '', locale_path


def make_locale_path(path, lang):
    """returns locale url - /home/ --> /en/home/"""
    return '/{0}{1}'.format(lang, path)


def redirect_to_language(url, lang_code):
    """change the language"""
    new_url = get_url_in_language(url, lang_code)
    translation.activate(lang_code)
    return HttpResponseRedirect(new_url)
