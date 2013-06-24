# -*- coding: utf-8 -*-

from modeltranslation.translator import translator, TranslationOptions
from coop_cms.models import NavNode, ArticleCategory, PieceOfHtml

class PieceOfHtmlTranslationOptions(TranslationOptions):
    fields = ('content',)

translator.register(PieceOfHtml, PieceOfHtmlTranslationOptions)


class NavNodeTranslationOptions(TranslationOptions):
    fields = ('label',)

translator.register(NavNode, NavNodeTranslationOptions)


class ArticleCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(ArticleCategory, ArticleCategoryTranslationOptions)
