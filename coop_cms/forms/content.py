# -*- coding: utf-8 -*-
"""forms"""

from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

import floppyforms as floppyforms

from ..models import Alias, Link, Document, MediaFilter, ImageSize
from ..widgets import ChosenSelectMultiple

from .fields import HidableMultipleChoiceField
from .navigation import WithNavigationModelForm


class MediaBaseAddMixin(object):

    def __init__(self, *args, **kwargs):
        super(MediaBaseAddMixin, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        # Media filters
        queryset1 = MediaFilter.objects.all()
        if queryset1.count():
            self.fields['filters'].choices = [(media_filter.id, media_filter.name) for media_filter in queryset1]
            try:
                self.fields['filters'].widget = ChosenSelectMultiple(
                    choices=self.fields['filters'].choices, force_template=True,
                )
            except NameError:
                # print 'No ChosenSelectMultiple'
                pass
        else:
            self.fields['filters'].widget = self.fields['filters'].hidden_widget()

    def clean_filters(self):
        """validation"""
        filters = self.cleaned_data['filters']
        return [MediaFilter.objects.get(id=pk) for pk in filters]


class AddImageForm(MediaBaseAddMixin, floppyforms.Form):
    """Form for adding new image"""

    image = floppyforms.ImageField(required=True, label=_('Image'),)
    descr = floppyforms.CharField(
        required=False,
        widget=floppyforms.TextInput(
            attrs={'size': '35', 'placeholder': _('Optional description'), }
        ),
        label=_('Description'),
    )
    copyright = floppyforms.CharField(required=False, label=_('copyright'))
    alt_text = floppyforms.CharField(required=False, label=_('alt text'))
    title = floppyforms.CharField(required=False, label=_('title'))
    filters = HidableMultipleChoiceField(
        required=False, label=_("Filters"), help_text=_("Choose between tags to find images more easily")
    )
    size = floppyforms.ChoiceField(
        required=False, label=_("Size"), help_text=_("Define a size if you want to resize the image")
    )

    def __init__(self, *args, **kwargs):
        super(AddImageForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        img_size_queryset = ImageSize.objects.all()
        if img_size_queryset.count():
            self.fields['size'].choices = [
                ('', '')
            ] + [
                (img_size.id, '{0}'.format(img_size)) for img_size in img_size_queryset
            ]
        else:
            self.fields['size'].widget = floppyforms.HiddenInput()

    def clean_size(self):
        """validation"""
        size_id = self.cleaned_data['size']
        if not size_id:
            return None
        try:
            return ImageSize.objects.get(id=size_id)
        except (ValueError, ImageSize.DoesNotExist):
            raise ValidationError(_("Invalid choice"))


class AddDocForm(MediaBaseAddMixin, forms.ModelForm):
    """add document form"""

    filters = floppyforms.MultipleChoiceField(
        required=False, label=_("Filters"), help_text=_("Choose between tags to find images more easily")
    )

    class Meta:
        model = Document
        fields = ('file', 'name', 'is_private', 'category')


class NewLinkForm(WithNavigationModelForm):
    """New link form"""
    class Meta:
        model = Link
        fields = ('title', 'url', 'sites', )
        widgets = {
            'sites': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(NewLinkForm, self).__init__(*args, **kwargs)
        self.fields['sites'].initial = Site.objects.filter(id=settings.SITE_ID)


class AliasAdminForm(forms.ModelForm):
    """New link form"""
    class Meta:
        model = Alias
        fields = ('path', 'sites', 'redirect_code', 'redirect_url', )

    def __init__(self, *args, **kwargs):
        super(AliasAdminForm, self).__init__(*args, **kwargs)
        self.fields['sites'].queryset = Site.objects.all()
        self.fields['sites'].initial = Site.objects.filter(id=settings.SITE_ID)
        site_choices = [(site.id, site.domain) for site in Site.objects.all()]
        self.fields['sites'].widget = ChosenSelectMultiple(choices=site_choices, force_template=True)
        self.fields['sites'].help_text = ''
