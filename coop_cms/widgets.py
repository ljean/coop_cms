# -*- coding: utf-8 -*-

from floppyforms.widgets import ClearableFileInput, Select, SelectMultiple, HiddenInput


class ReadOnlyInput(HiddenInput):
    template_name = 'coop_cms/widgets/readonlyinput.html'

class ImageEdit(ClearableFileInput):
    template_name = 'coop_cms/widgets/imageedit.html'
    
    def __init__(self, update_url, thumbnail_src, *args, **kwargs):
        super(ImageEdit, self).__init__(*args, **kwargs)
        self._extra_context = {
            'update_url': update_url,
            'thumbnail_src': thumbnail_src
        }
        
    def get_context(self, *args, **kwargs):
        context = super(ImageEdit, self).get_context(*args, **kwargs)
        context.update(self._extra_context)
        return context
    
class ChosenWidgetMixin(object):

    class Media:
        js = (
            "{0}?v=1".format("chosen/chosen.jquery.min.js"),
        )
        css = {
            "all": ("{0}?v=1".format("chosen/chosen.css")),
        }

    def __init__(self, attrs=None, *args, **kwargs):
        chosen_css = "chosen-select"
        
        if not attrs:
            attrs = {}
        attrs['data-placeholder'] = kwargs.pop('overlay', None)
        css_class = u"{0}".format(attrs.get("class", ""))
        if css_class:
            if not chosen_css in css_class:
                css_class += (" " + chosen_css)
        else:
            css_class = chosen_css
            
        super(ChosenWidgetMixin, self).__init__(attrs, *args, **kwargs)

class ChosenSelectMultiple(ChosenWidgetMixin, SelectMultiple):
    pass

class ChosenSelect(ChosenWidgetMixin, Select):
    pass
