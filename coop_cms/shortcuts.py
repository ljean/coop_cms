# -*- coding: utf-8 -*-
"""utilities for developpers"""

from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.http import Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import get_object_or_404

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
    try:
        return article_class.objects.get(slug=slug, **kwargs)
    except article_class.DoesNotExist:
        # if modeltranslation is installed,
        # if no article correspond to the current language article
        # try to look for slug in default language
        if is_localized():

            from modeltranslation import settings as mt_settings
            from modeltranslation.utils import build_localized_fieldname

            fallback_languages = []
            if current_lang:
                fallback_languages += [current_lang, ]
            if force_lang:
                fallback_languages += [force_lang, ]

            mt_fallbacks = getattr(settings, 'MODELTRANSLATION_FALLBACK_LANGUAGES', None)
            if mt_fallbacks is None:
                fallback_languages += [mt_settings.DEFAULT_LANGUAGE, ]
            else:
                if isinstance(mt_fallbacks, dict):
                    if current_lang in mt_fallbacks:
                        fallback_languages += list(mt_fallbacks[current_lang])
                    else:
                        fallback_languages += list(mt_fallbacks.get('default', []))
                else:
                    fallback_languages += list(mt_fallbacks)

            for lang in fallback_languages:
                field_name = build_localized_fieldname('slug', lang)
                try:
                    lookup = kwargs.copy()
                    lookup.update({field_name: slug})
                    return article_class.objects.get(**lookup)
                except article_class.DoesNotExist:
                    pass

        # Not found
        raise article_class.DoesNotExist()


def get_article_or_404(slug, **kwargs):
    """get article or 404"""
    article_class = get_article_class()
    try:
        return get_article(slug, **kwargs)
    except article_class.DoesNotExist:
        raise Http404


def get_headlines(article=None, editable=False):
    """get articles to display on homepage"""
    article_class = get_article_class()
    if (article and article.is_homepage) or (article is None):
        queryset = article_class.objects.filter(headline=True)
        if editable:
            queryset = queryset.filter(publication__in=(BaseArticle.PUBLISHED, BaseArticle.DRAFT))
        else:
            queryset = queryset.filter(publication=BaseArticle.PUBLISHED)
        return queryset.filter(sites=Site.objects.get_current()).order_by("-publication_date")
    return article_class.objects.none()


def redirect_if_alias(path):
    """redirect if path correspond to an alias"""
    article_class = get_article_class()
    site = Site.objects.get_current()

    # look for an article corresponding to this path. For example if trailing slash is missing in the url
    try:
        article = article_class.objects.get(slug=path, sites=site, publication=BaseArticle.PUBLISHED)
    except article_class.DoesNotExist:
        article = None

    if article:
        return HttpResponseRedirect(article.get_absolute_url())

    else:

        # look for a regular alias
        try:
            alias = Alias.objects.get(path=path, sites=site)
        except Alias.DoesNotExist:
            if path and path[-1] == '/':
                alias = get_object_or_404(Alias, path=path[:-1], sites=site)
            else:
                alias = None

        if alias and alias.redirect_url:
            if alias.redirect_code == 301:
                return HttpResponsePermanentRedirect(alias.redirect_url)
            else:
                return HttpResponseRedirect(alias.redirect_url)
        else:
            raise Http404
