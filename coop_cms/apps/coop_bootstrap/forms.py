import floppyforms as forms

class _BootstrapableForm(object):
    
    def _bs_patch_field_class(self):
        for field_name in self.fields:
            field = self.fields[field_name]
            if field.widget.attrs.has_key('class'):
                val = field.widget.attrs['class']
                field.widget.attrs['class'] = val + " form-control"
            else:
                field.widget.attrs['class'] = "form-control"
    

class BootstrapForm(forms.Form, _BootstrapableForm):
    
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()

class BootstrapModelForm(forms.ModelForm, _BootstrapableForm):
    
    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()

