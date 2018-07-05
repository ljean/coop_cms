# -*- coding: utf-8 -*-
"""Boptstrap-css friendly forms"""

from __future__ import unicode_literals

import types

import floppyforms.__future__ as forms

from coop_cms.templatetags.coop_utils import is_checkbox


def _build_attrs(widget, base_attrs, extra_attrs=None, **kwargs):
    """Patch > Helper function for building an attribute dictionary."""
    attrs = base_attrs.copy()
    if widget.attrs:
        attrs.update(widget.attrs)
    if 'class' in attrs:
        val = attrs['class']
        attrs['class'] = val + " form-control"
    else:
        attrs['class'] = "form-control"
    if extra_attrs is not None:
        attrs.update(extra_attrs)
    if kwargs:
        attrs.update(kwargs)
    return attrs


class BootstrapableMixin(object):

    def _bs_patch_field_class(self):
        """Patch fields for adding form-control class to widget"""
        for field_name in self.fields:
            field = self.fields[field_name]
            self._bs_patch_field(field)

    @staticmethod
    def _bs_patch_field(field):
        if not is_checkbox(field):
            # replace the `build_attrs` method of the widget with a custom version whic adds the
            # form-control class to attrs
            field.widget.build_attrs = types.MethodType(_build_attrs, field.widget)


class Form(forms.Form, BootstrapableMixin):

    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()


class ModelForm(forms.ModelForm, BootstrapableMixin):

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self._bs_patch_field_class()
