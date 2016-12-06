# -*- coding: utf-8 -*-
"""widgets"""

from floppyforms.widgets import ClearableFileInput, Select, SelectMultiple, Input

from coop_cms.utils import get_text_from_template


class ReadOnlyInput(Input):
    """readonly input"""
    template_name = 'coop_cms/widgets/readonlyinput.html'


class ImageEdit(ClearableFileInput):
    """image edit"""
    template_name = 'coop_cms/widgets/imageedit.html'
    
    def __init__(self, update_url, thumbnail_src, *args, **kwargs):
        super(ImageEdit, self).__init__(*args, **kwargs)
        self._extra_context = {
            'update_url': update_url,
            'thumbnail_src': thumbnail_src,
            'extra_classes': get_text_from_template("coop_cms/widgets/_imageedit_cssclass.html"),
        }
        
    def get_context(self, *args, **kwargs):
        """get context"""
        context = super(ImageEdit, self).get_context(*args, **kwargs)
        context.update(self._extra_context)
        return context


class ChosenWidgetMixin(object):
    """chosen jquery widget"""

    def _patch(self, kwargs):

        self._extra_context = {}
        if kwargs.pop("force_template", False):
            # chosen inherit from super template
            self._extra_context['super_template'] = self.template_name
            self.template_name = 'coop_cms/widgets/chosen.html'

        self._extra_context['on_popup'] = kwargs.pop("on_popup", False)

        return kwargs


class ChosenSelectMultiple(ChosenWidgetMixin, SelectMultiple):
    """chosen select multiple"""

    def __init__(self, attrs=None, *args, **kwargs):

        kwargs = self._patch(kwargs)

        if not attrs:
            attrs = {}
        attrs['data-placeholder'] = kwargs.pop('overlay', None)
        super(ChosenSelectMultiple, self).__init__(attrs, *args, **kwargs)

    def get_context(self, *args, **kwargs):
        """context"""
        context = super(ChosenSelectMultiple, self).get_context(*args, **kwargs)  # pylint: disable=E1002
        context.update(self._extra_context)
        return context

    class Media:
        """css and js required by widget"""
        js = (
            "{0}?v=1".format("chosen/chosen.jquery.min.js"),
        )
        css = {
            "all": ("{0}?v=1".format("chosen/chosen.css"),),
        }


class ChosenSelect(ChosenWidgetMixin, Select):
    """chosen select"""

    def __init__(self, attrs=None, *args, **kwargs):
        kwargs = self._patch(kwargs)

        if not attrs:
            attrs = {}
        attrs['data-placeholder'] = kwargs.pop('overlay', None)
        super(ChosenSelect, self).__init__(attrs, *args, **kwargs)

    def get_context(self, *args, **kwargs):
        """context"""
        context = super(ChosenSelect, self).get_context(*args, **kwargs)  # pylint: disable=E1002
        context.update(self._extra_context)
        return context

    class Media:
        """css and js required by widget"""
        js = (
            "{0}?v=1".format("chosen/chosen.jquery.min.js"),
        )
        css = {
            "all": ("{0}?v=1".format("chosen/chosen.css"),),
        }