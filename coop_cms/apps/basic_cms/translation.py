# -*- coding: utf-8 -*-

from modeltranslation.translator import translator, TranslationOptions
from coop_cms.apps.basic_cms.models import Article

class ArticleTranslationOptions(TranslationOptions):
    fields = ('slug', 'title', 'content', 'summary', 'subtitle')

translator.register(Article, ArticleTranslationOptions)