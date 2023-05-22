# -*- coding: utf-8 -*-
"""forms"""

import floppyforms as forms

from coop_html_editor.widgets import get_inline_html_widget

from ...forms.articles import NewArticleForm, ArticleSettingsForm
from ...forms.base import InlineHtmlEditableModelForm
from ...forms.newsletters import NewsletterSettingsForm

from .models import TestClass


class TestClassForm(InlineHtmlEditableModelForm):
    """for unit-testing"""
    class Meta:
        model = TestClass
        fields = ('field1', 'field2', 'field3', 'bool_field', 'int_field', 'float_field')
        widgets = {
            'field2': get_inline_html_widget(),
        }
        no_inline_html_widgets = ('field2', 'field3', 'bool_field', 'int_field', 'float_field')


class MyNewArticleForm(NewArticleForm):
    """for unit-testing"""
    dummy = forms.CharField(required=False)


class MyArticleSettingsForm(ArticleSettingsForm):
    """for unit-testing"""
    dummy = forms.CharField(required=False)


class MyNewsletterSettingsForm(NewsletterSettingsForm):
    """for unit-testing"""
    dummy = forms.CharField(required=False)
