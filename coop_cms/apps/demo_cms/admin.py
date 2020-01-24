# -*- coding: utf-8 -*-
"""
Admin site
"""

from django.contrib import admin

from coop_cms.admin import ArticleAdmin as CmsArticleAdmin
from coop_cms.settings import get_article_class


article_class = get_article_class()

# Replace the default Article admin
admin.site.unregister(article_class)


@admin.register(article_class)
class ArticleAdmin(CmsArticleAdmin):
    """Custom Article admin"""
    fieldsets = CmsArticleAdmin.fieldsets + (
        ('Misc', {'fields': ('author',)}),
    )
