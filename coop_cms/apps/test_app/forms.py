# -*- coding: utf-8 -*-
"""forms"""

from __future__ import unicode_literals

import floppyforms.__future__ as forms

from coop_html_editor.widgets import get_inline_html_widget

from coop_cms.apps.test_app.models import TestClass
from coop_cms.forms.articles import NewArticleForm, ArticleSettingsForm
from coop_cms.forms.base import InlineHtmlEditableModelForm
from coop_cms.forms.newsletters import NewsletterSettingsForm


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
