# -*- coding: utf-8 -*-
"""
Example of custom forms
"""

import floppyforms.__future__ as forms

from coop_cms.forms.articles import ArticleForm as CmsArticleForm
from coop_cms.forms.newsletters import NewsletterForm
from coop_cms.settings import get_article_class
from coop_cms.models import ArticleCategory


class ArticleForm(CmsArticleForm):
    """Custom article form"""

    class Meta(CmsArticleForm.Meta):
        model = get_article_class()
        fields = CmsArticleForm.Meta.fields + ('author',)


class SortableNewsletterForm(NewsletterForm):
    """Example of newsletter form"""
    # cleaned_data = None

    sortable = forms.CharField(required=False, widget=forms.HiddenInput())

    class Media(NewsletterForm.Media):
        js = NewsletterForm.Media.js + ('js/jquery.sortElements.js',)

    def save(self, *args, **kwargs):
        """override save"""
        ret = super(SortableNewsletterForm, self).save(*args, **kwargs)

        order = self.cleaned_data['sortable']
        if order:
            order = [int(x) for x in order.split(';')]
            for art_id in order:
                section = ArticleCategory.objects.get(id=art_id)
                section.ordering = order.index(art_id) + 1
                section.save()

        return ret
