# -*- coding: utf-8 -*-
"""modeltranslation settings"""

from modeltranslation.translator import translator, TranslationOptions # pylint: disable=F0401

from coop_cms.models import Alias, ArticleCategory, Fragment, NavNode, Newsletter, PieceOfHtml, SiteSettings


class PieceOfHtmlTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('content',)
translator.register(PieceOfHtml, PieceOfHtmlTranslationOptions)


class FragmentTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('content',)
translator.register(Fragment, FragmentTranslationOptions)


class NavNodeTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('label',)
translator.register(NavNode, NavNodeTranslationOptions)


class ArticleCategoryTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('name',)
translator.register(ArticleCategory, ArticleCategoryTranslationOptions)


class SiteSettingsTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('homepage_url',)
translator.register(SiteSettings, SiteSettingsTranslationOptions)


class AliasTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('path', 'redirect_url',)
translator.register(Alias, AliasTranslationOptions)


class NewsletterTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('subject', 'content',)
translator.register(Newsletter, NewsletterTranslationOptions)
