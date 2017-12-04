# -*- coding: utf-8 -*-
"""forms"""

from __future__ import unicode_literals

from six import string_types

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

import floppyforms.__future__ as floppyforms

from coop_cms.models import Fragment, FragmentType


class BaseFragmentForm(floppyforms.ModelForm):
    """Base class for AddFragmentForm and EditFragmentForm"""

    class Media:
        css = {
            'all': ('chosen/chosen.css', ),
        }
        js = (
            'chosen/chosen.jquery.js',
        )

    def post_init(self, all_classes=False):
        """init"""
        try:
            instance_fragment_type = self.instance.type
        except FragmentType.DoesNotExist:
            instance_fragment_type = None

        if instance_fragment_type or all_classes:
            if instance_fragment_type:
                css_classes = instance_fragment_type.allowed_css_classes.split(',')
            else:
                css_classes = []
                for fragment_type in FragmentType.objects.all():
                    fragment_classes = fragment_type.allowed_css_classes.split(',')
                    for css_class in fragment_classes:
                        if css_class not in css_classes:
                            css_classes.append(css_class)
            if css_classes:
                choices = [('', '')] + [(x, x) for x in css_classes]
                self.fields['css_class'].widget = floppyforms.SelectMultiple(
                    choices=choices,
                    attrs={"class": "chosen-select", "data-placeholder": _("Select CSS classes to apply")}
                )
            else:
                self.fields['css_class'].widget = floppyforms.HiddenInput()
        else:
            self.fields['css_class'].widget = floppyforms.HiddenInput()

    def clean_css_class(self):
        """clean css_class field"""
        instance_fragment_type = self.cleaned_data['type']

        allowed_classes = instance_fragment_type.allowed_css_classes.split(',') if instance_fragment_type else []
        values = self.cleaned_data['css_class']

        if isinstance(values, string_types):
            values = values.strip("[]").split(",")
            values = [x.replace("u'", "").replace('u"', '').strip("\"' ") for x in values]
            values = [x for x in values if x]

        for value in values:
            if not value in allowed_classes:
                raise ValidationError(_("Invalid class '{0}'").format(value))

        return " ".join(values)

    def clean(self):
        ret = super(BaseFragmentForm, self).clean()

        # Check that if no filter is set : the name and type are unique together
        queryset = Fragment.objects.filter(
            name=self.cleaned_data.get('name', ''),
            type=self.cleaned_data.get('type'),
        )
        fragment_filter = self.cleaned_data.get('filter')
        if fragment_filter is None:
            queryset = queryset.filter(filter__isnull=True)
            if queryset.count():
                raise forms.ValidationError(_(u"A fragment with this name already exists"))

        return ret


class AddFragmentForm(BaseFragmentForm):
    """Add fragment"""
    class Meta:
        model = Fragment
        fields = ('type', 'name', 'css_class', 'position', 'filter', )
        widgets = {
            "filter": forms.HiddenInput(),
        }

    def __init__(self, data=None, *args, **kwargs):
        super(AddFragmentForm, self).__init__(data, *args, **kwargs)  # pylint: disable=E1002
        self.post_init(all_classes=True)


class EditFragmentForm(BaseFragmentForm):
    """Edit fragment"""
    delete_me = floppyforms.BooleanField(label=_("delete"), required=False)

    class Meta:
        model = Fragment
        fields = ('type', 'filter', 'name', 'css_class', 'position', )
        widgets = {
            "type": forms.HiddenInput(),
            "filter": forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            instance.css_class = instance.css_class.split(" ")
        super(EditFragmentForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.post_init()

    def save(self, *args, **kwargs):
        """delete """
        if self.cleaned_data['delete_me']:
            self.instance.delete()
            return None
        return super(EditFragmentForm, self).save(*args, **kwargs)  # pylint: disable=E1002
