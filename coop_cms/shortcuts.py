# -*- coding: utf-8 -*-
"""utilities for developpers"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language

from coop_cms.models import BaseArticle, Alias
from coop_cms.settings import get_article_class, is_localized
from coop_cms.utils import strip_locale_path


def get_article_slug(*args, **kwargs):
    """slugify"""
    slug = reverse(*args, **kwargs)
    lang, slug = strip_locale_path(slug)
    return slug.strip('/')


def get_article(slug, current_lang=None, force_lang=None, all_langs=False, **kwargs):
    """get article"""
    article_class = get_article_class()
    current_lang = get_language()
    try:
        return article_class.objects.get(slug=slug, **kwargs)
    except article_class.DoesNotExist:
        #if modeltranslation is installed,
        #if no article correspond to the current language article
        #try to look for slug in default language
        if is_localized():
            from modeltranslation import settings as mt_settings
            default_lang = mt_settings.DEFAULT_LANGUAGE
            try:
                lang = force_lang
                if not lang:
                    if current_lang != default_lang:
                        lang = default_lang
                if lang:
                    kwargs.update({'slug_{0}'.format(lang): slug})
                    return article_class.objects.get(**kwargs)
                else:
                    raise article_class.DoesNotExist()
            except article_class.DoesNotExist:
                if current_lang == default_lang:
                    # Try to find in another lang
                    # The article might be created in another language than the default one
                    for (lang_code, lang_name) in settings.LANGUAGES:
                        key = 'slug_{0}'.format(lang_code)
                        try:
                            kwargs.update({key: slug})
                            return article_class.objects.get(**kwargs)
                        except article_class.DoesNotExist:
                            kwargs.pop(key)
                raise article_class.DoesNotExist()
        raise  # re-raise previous error


def get_article_or_404(slug, **kwargs):
    """get article or 404"""
    article_class = get_article_class()
    try:
        return get_article(slug, **kwargs)
    except article_class.DoesNotExist:
        raise Http404


def get_headlines(article, editable=False):
    """get articles to display on homepage"""
    article_class = get_article_class()
    if article.is_homepage:
        queryset = article_class.objects.filter(headline=True)
        if editable:
            queryset = queryset.filter(publication__in=(BaseArticle.PUBLISHED, BaseArticle.DRAFT))
        else:
            queryset = queryset.filter(publication=BaseArticle.PUBLISHED)
        return queryset.filter(sites=Site.objects.get_current()).order_by("-publication_date")
    return article_class.objects.none()


def redirect_if_alias(path):
    """redirect if path correspond to an alias"""
    alias = get_object_or_404(Alias, path=path)
    if alias.redirect_url:
        return HttpResponsePermanentRedirect(alias.redirect_url)
    else:
        raise Http404