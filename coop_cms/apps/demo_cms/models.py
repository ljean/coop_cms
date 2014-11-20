# -*- coding: utf-8 -*-
"""
models for demo application : how to customize an article
"""

from django.contrib.auth.models import User
from django.db import models

from coop_cms.models import BaseArticle


class Article(BaseArticle):
    """Example of custom article: add an author field"""
    author = models.ForeignKey(User, blank=True, default=None, null=True)

    def __unicode__(self):
        return u"{0} - {1}".format(self.author, super(Article, self).__unicode__())


class ModeratedArticle(Article):
    """Moderated Article : only the  superuser can publish"""

    class Meta:
        proxy = True

    def can_publish_article(self, user):
        """return true if the user can publish the article: only superuser is allowed"""
        return user.is_superuser

    def __unicode__(self):
        return super(ModeratedArticle, self).__unicode__()


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

    def __unicode__(self):
        return super(PrivateArticle, self).__unicode__()
