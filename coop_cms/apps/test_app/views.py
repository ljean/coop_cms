# -*- coding: utf-8 -*-
"""for unit-testing"""

from __future__ import unicode_literals

from coop_cms.apps.test_app.models import TestClass
from coop_cms.apps.test_app.forms import TestClassForm

from coop_cms.generic_views import EditableObjectView, ListView, EditableFormsetView


class TestClassListView(ListView):
    """for unit-testing"""
    model = TestClass
    template_name = "coop_cms/test_app/list.html"
    ordering = 'other_field'


class TestClassDetailView(EditableObjectView):
    """for unit-testing"""
    model = TestClass
    edit_mode = False
    form_class = TestClassForm
    template_name = "coop_cms/test_app/detail.html"


class TestClassEditView(TestClassDetailView):
    """for unit-testing"""
    edit_mode = True


class TestClassFormsetView(EditableFormsetView):
    """for unit-testing"""
    model = TestClass
    edit_mode = False
    form_class = TestClassForm
    template_name = "coop_cms/test_app/formset.html"
    success_view_name = 'coop_cms_testapp_formset'


class TestClassFormsetEditView(TestClassFormsetView):
    """for unit-testing"""
    edit_mode = True
