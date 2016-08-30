# -*- coding: utf-8 -*-
"""forms"""

import floppyforms as forms

from coop_html_editor.widgets import get_inline_html_widget

from coop_cms.apps.test_app.models import TestClass
from coop_cms.forms import InlineHtmlEditableModelForm, NewArticleForm, ArticleSettingsForm, NewsletterSettingsForm


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
