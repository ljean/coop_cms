# -*- coding: utf-8 -*-

from modeltranslation.translator import translator, TranslationOptions
from coop_cms.models import NavNode, ArticleCategory, PieceOfHtml, Fragment, SiteSettings, Alias

class PieceOfHtmlTranslationOptions(TranslationOptions):
    fields = ('content',)
translator.register(PieceOfHtml, PieceOfHtmlTranslationOptions)

class FragmentTranslationOptions(TranslationOptions):
    fields = ('content',)
translator.register(Fragment, FragmentTranslationOptions)


class NavNodeTranslationOptions(TranslationOptions):
    fields = ('label',)
translator.register(NavNode, NavNodeTranslationOptions)


class ArticleCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(ArticleCategory, ArticleCategoryTranslationOptions)


class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ('homepage_url',)
translator.register(SiteSettings, SiteSettingsTranslationOptions)

class AliasTranslationOptions(TranslationOptions):
    fields = ('path', 'redirect_url',)
translator.register(Alias, AliasTranslationOptions)
