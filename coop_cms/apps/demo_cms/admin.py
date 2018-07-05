# -*- coding: utf-8 -*-
"""
Admin site
"""

from __future__ import unicode_literals

from django.contrib import admin

from coop_cms.admin import ArticleAdmin as CmsArticleAdmin
from coop_cms.settings import get_article_class


class ArticleAdmin(CmsArticleAdmin):
    """Custom Article admin"""
    fieldsets = CmsArticleAdmin.fieldsets + (
        ('Misc', {'fields': ('author',)}),
    )

# Replace the default Article admin
admin.site.unregister(get_article_class())
admin.site.register(get_article_class(), ArticleAdmin)
