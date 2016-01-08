# -*- coding: utf-8 -*-

"""
modeltranslation config file : which field to be translatable
"""

from modeltranslation.translator import translator, TranslationOptions  # pylint: disable=F0401

from coop_cms.apps.basic_cms.models import Article


class ArticleTranslationOptions(TranslationOptions):
    """Translate article"""
    fields = ('slug', 'title', 'content', 'summary', 'subtitle')

translator.register(Article, ArticleTranslationOptions)
