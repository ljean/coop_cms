# -*- coding: utf-8 -*-

import floppyforms as forms
from djaloha.widgets import AlohaInput
from models import TestClass

class TestClassForm(forms.ModelForm):
    
    class Meta:
        model = TestClass
        fields = ('field1', 'field2',)
        widgets = {
            'field1': AlohaInput(),
            'field2': AlohaInput(),
        }