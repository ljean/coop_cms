# -*- coding: utf-8 -*-

from models import TestClass
from forms import TestClassForm

from coop_cms.generic_views import EditableObjectView, ListView, EditableFormsetView

class TestClassListView(ListView):
    model = TestClass
    template_name = "coop_cms/test_app/list.html"
    ordering = 'other_field'

class TestClassDetailView(EditableObjectView):
    model = TestClass
    edit_mode = False
    form_class = TestClassForm
    template_name = "coop_cms/test_app/detail.html"
    
class TestClassEditView(TestClassDetailView):
    edit_mode = True
    
class TestClassFormsetView(EditableFormsetView):
    model = TestClass
    edit_mode = False
    form_class = TestClassForm
    template_name = "coop_cms/test_app/formset.html"
    success_view_name = 'coop_cms_testapp_formset'
    
class TestClassFormsetEditView(TestClassFormsetView):
    edit_mode = True
    