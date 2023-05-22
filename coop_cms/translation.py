# -*- coding: utf-8 -*-
"""modeltranslation settings"""

from modeltranslation.translator import translator, TranslationOptions  # pylint: disable=F0401

from .models import (
    Alias, ArticleCategory, Fragment, NavNode, Newsletter, PieceOfHtml, SiteSettings, validate_slug, Link
)
from .settings import get_eastern_languages


class PieceOfHtmlTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('content', )


class FragmentTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('content', )


class NavNodeTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('label', )


class ArticleCategoryTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('name', )


class SiteSettingsTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('homepage_url', 'homepage_article', )


class AliasTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('path', 'redirect_url', )


class NewsletterTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('subject', 'content',)


class LinkTranslationOptions(TranslationOptions):
    """translation"""
    fields = ('url',)


class BaseArticleTranslationOptions(TranslationOptions):
    """
    Handle eastern languages (russian, chinese, japanese...) and slugs : Do not validate in this case
    Inherit the ArticleTranslationOptions from this base class
    """

    class SlugValidator(object):

        def __init__(self, is_eastern_language):
            self.is_eastern_language = is_eastern_language

        def __call__(self, value):
            if not self.is_eastern_language:
                validate_slug(value)

    def add_translation_field(self, field, translation_field):
        """
        Add a new translation field to both fields dicts.
        """
        # Patch the slug field in order not to validate slug if easten
        if field == 'slug':  # and translation_field.language in get_eastern_languages():
            if validate_slug in translation_field.validators:
                translation_field.validators.remove(validate_slug)
            translation_field.validators = [
                BaseArticleTranslationOptions.SlugValidator(translation_field.language in get_eastern_languages())
            ] + translation_field.validators
        super(BaseArticleTranslationOptions, self).add_translation_field(field, translation_field)


translator.register(PieceOfHtml, PieceOfHtmlTranslationOptions)
translator.register(Fragment, FragmentTranslationOptions)
translator.register(NavNode, NavNodeTranslationOptions)
translator.register(ArticleCategory, ArticleCategoryTranslationOptions)
translator.register(SiteSettings, SiteSettingsTranslationOptions)
translator.register(Alias, AliasTranslationOptions)
translator.register(Newsletter, NewsletterTranslationOptions)
translator.register(Link, LinkTranslationOptions)
