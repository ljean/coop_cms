# -*- coding: utf-8 -*-
"""forms"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

import floppyforms

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
                    attrs={"class": "chosen-select", "data-placeholder": _(u"Select CSS classes to apply")}
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
        if type(values) in (unicode, str):
            values = values.strip("[]").split(",")
            values = [x.replace("u'", "").replace('u"', '').strip("\"' ") for x in values]
            values = [x for x in values if x]
        for value in values:
            if not value in allowed_classes:
                raise ValidationError(_(u"Invalid class '{0}'").format(value))
        return u" ".join(values)


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
    delete_me = floppyforms.BooleanField(label=_(u"delete"), required=False)

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
