# -*- coding: utf-8 -*-
"""
models for demo application : how to customize an article
"""

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from coop_cms.models import BaseArticle


@python_2_unicode_compatible
class Article(BaseArticle):
    """Example of custom article: add an author field"""
    author = models.ForeignKey(User, blank=True, default=None, null=True)

    def __str__(self):
        return "{0} - {1}".format(self.author, super(Article, self).__str__())


@python_2_unicode_compatible
class ModeratedArticle(Article):
    """Moderated Article : only the  superuser can publish"""

    class Meta:
        proxy = True

    def can_publish_article(self, user):
        """return true if the user can publish the article: only superuser is allowed"""
        return user.is_superuser

    def __str__(self):
        return super(ModeratedArticle, self).__str__()


@python_2_unicode_compatible
class PrivateArticle(Article):
    """Article : only the author can access"""

    class Meta:
        proxy = True

    def can_view_article(self, user):
        """True if user can view: here only the article author"""
        return self.author == user

    def can_edit_article(self, user):
        """True if user can edit: here only the article author"""
        return self.author == user

    def can_publish_article(self, user):
        """True if user can publish: here only the article author"""
        return self.author == user

    def __str__(self):
        return super(PrivateArticle, self).__str__()
