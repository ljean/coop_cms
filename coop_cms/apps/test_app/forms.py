# -*- coding: utf-8 -*-

import floppyforms as forms
from djaloha.widgets import AlohaInput
from models import TestClass
from coop_cms.forms import AlohaEditableModelForm

class TestClassForm(AlohaEditableModelForm):
    
    class Meta:
        model = TestClass
        fields = ('field1', 'field2', 'field3') 
        widgets = {
            'field2': AlohaInput(),
        }
        no_aloha_widgets = ('field2', 'field3',)