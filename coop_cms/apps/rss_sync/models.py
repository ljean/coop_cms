# -*- coding: utf-8 -*-
"""
models
"""

from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class RssSource(models.Model):
    """a Rss feed to use as source of items (which are used to create CMS articles)"""

    url = models.URLField(_('url'), unique=True)
    title = models.CharField(_("title"), max_length=200, blank=True, default="")
    last_collect = models.DateTimeField(_("last collect"), blank=True, null=True)

    def get_absolute_url(self):
        """absolute url"""
        return self.url

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = _('RSS source')
        verbose_name_plural = _('RSS sources')


@python_2_unicode_compatible
class RssItem(models.Model):
    """a Rss item that can be used to create a CMS article"""

    source = models.ForeignKey(RssSource)
    link = models.URLField(_('link'))
    title = models.CharField(_("title"), max_length=200, blank=True)
    summary = models.TextField(_("summary"), blank=True)
    author = models.CharField(_("author"), max_length=200, blank=True)
    updated = models.DateTimeField(_("updated"), blank=True, null=True)
    processed = models.BooleanField(_("processed"), default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('RSS item')
        verbose_name_plural = _('RSS items')
