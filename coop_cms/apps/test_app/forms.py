# -*- coding: utf-8 -*-
"""forms"""

import floppyforms as forms

from djaloha.widgets import AlohaInput

from coop_cms.apps.test_app.models import TestClass
from coop_cms.forms import AlohaEditableModelForm, NewArticleForm, ArticleSettingsForm, NewsletterSettingsForm


class TestClassForm(AlohaEditableModelForm):
    """for unit-testing"""
    class Meta:
        model = TestClass
        fields = ('field1', 'field2', 'field3', 'bool_field', 'int_field', 'float_field')
        widgets = {
            'field2': AlohaInput(),
        }
        no_aloha_widgets = ('field2', 'field3', 'bool_field', 'int_field', 'float_field')


class MyNewArticleForm(NewArticleForm):
    """for unit-testing"""
    dummy = forms.CharField(required=False)


class MyArticleSettingsForm(ArticleSettingsForm):
    """for unit-testing"""
    dummy = forms.CharField(required=False)


class MyNewsletterSettingsForm(NewsletterSettingsForm):
    """for unit-testing"""
    dummy = forms.CharField(required=False)
