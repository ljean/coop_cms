# -*- coding: utf-8 -*-
"""forms"""

from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from coop_cms.models import NavType, NavNode, get_navigable_type_choices
from coop_cms.settings import get_navigable_content_types, get_article_class, get_navtree_class
from coop_cms.widgets import GenericFieldRawIdWidget


class NavTypeForm(forms.ModelForm):
    """Navigation Type Form"""

    def __init__(self, *args, **kwargs):
        super(NavTypeForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.fields['content_type'].widget = forms.Select(choices=get_navigable_content_types())

    def clean_label_rule(self):
        """validation of label_rule"""
        rule = self.cleaned_data['label_rule']
        if rule == NavType.LABEL_USE_GET_LABEL:
            content_type = self.cleaned_data['content_type']
            if not 'get_label' in dir(content_type.model_class()):
                raise ValidationError(
                    _("Invalid rule for this content type: The object class doesn't have a get_label method")
                )
        return rule

    class Meta:
        model = NavType
        fields = ('content_type', 'search_field', 'label_rule')


class NavNodeAdminForm(forms.ModelForm):
    """Navigation Type Form"""

    def __init__(self, *args, **kwargs):
        super(NavNodeAdminForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.fields['content_type'].widget = forms.Select(choices=get_navigable_type_choices())
        self.fields['object_id'].widget = GenericFieldRawIdWidget(kwargs.get('instance', None))

    class Meta:
        model = NavNode
        exclude = []


def get_node_choices():
    """used for node selection in article settings form"""
    prefix = "--"
    choices = [(None, _('<not in navigation>'))]
    for tree in get_navtree_class().objects.all():
        choices.append((-tree.id, tree.name))
        for root_node in NavNode.objects.filter(tree=tree, parent__isnull=True).order_by('ordering'):
            for (progeny, level) in root_node.get_progeny():
                choices.append((progeny.id, prefix * (level + 1) + progeny.label))
    return choices


def get_navigation_parent_help_text():
    """help text"""
    return get_article_class().navigation_parent.__doc__


class WithNavigationModelForm(forms.ModelForm):
    """Base class for every setting form which needs to display an Navigation field"""
    navigation_parent = forms.ChoiceField()
    
    def __init__(self, *args, **kwargs):
        super(WithNavigationModelForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.fields['navigation_parent'] = forms.ChoiceField(
            choices=get_node_choices(), required=False, help_text=get_navigation_parent_help_text()
        )
        if self.instance:
            self.fields['navigation_parent'].initial = self.instance.navigation_parent

    def clean_navigation_parent(self):
        """validation"""
        parent_id = self.cleaned_data['navigation_parent']
        parent_id = int(parent_id) if (parent_id != '' and parent_id != 'None') else None
        return parent_id

    def save(self, commit=True):
        """save: manage navigation field"""
        instance = super(WithNavigationModelForm, self).save(commit=False)  # pylint: disable=E1002
        parent_id = self.cleaned_data['navigation_parent']
        if instance.id:
            if instance.navigation_parent != parent_id:
                instance.navigation_parent = parent_id
        else:
            setattr(instance, '_navigation_parent', parent_id)
        if commit:
            instance.save()
        return instance
