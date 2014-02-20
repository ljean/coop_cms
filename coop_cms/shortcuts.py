# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.urlresolvers import reverse
from coop_cms.settings import get_article_class, is_localized, get_newsletter_context_callbacks
from coop_cms.models import BaseArticle, Alias
from django.utils.translation import get_language
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

def get_article_slug(*args, **kwargs):
    slug = reverse(*args, **kwargs)
    if 'localeurl' in settings.INSTALLED_APPS:
        #If localeurl is installed reverse is patched
        #We must remove the lang prefix
        from localeurl.utils import strip_path
        lang, slug = strip_path(slug)
    return slug.strip('/')

def get_article(slug, current_lang=None, force_lang=None, all_langs=False, **kwargs):
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
            try:
                lang = force_lang
                if not lang:
                    current_lang = get_language()
                    if current_lang != default_lang:
                        lang = default_lang
                if lang:
                    kwargs.update({'slug_{0}'.format(lang): slug})
                    return Article.objects.get(**kwargs)
                else:
                    raise Article.DoesNotExist()
            except Article.DoesNotExist:
                #Try to find in another lang
                #The article might be created in another language than the default one
                for (l, n) in settings.LANGUAGES:
                    key = 'slug_{0}'.format(l)
                    try:
                        kwargs.update({key: slug})
                        return Article.objects.get(**kwargs)
                    except Article.DoesNotExist:
                        kwargs.pop(key)
                raise Article.DoesNotExist()
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