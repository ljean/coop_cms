# -*- coding: utf-8 -*-

from models import TestClass
from forms import TestClassForm

from coop_cms.generic_views import EditableObjectView, ListView

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
    