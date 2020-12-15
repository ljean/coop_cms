# -*- coding: utf-8 -*-
"""forms"""

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.timezone import now as dt_now
from django.utils.translation import ugettext as _, ugettext_lazy

import floppyforms.__future__ as floppyforms

from coop_cms.forms.base import InlineHtmlEditableModelForm
from coop_cms.bs_forms import Form as BsForm
from coop_cms.models import Newsletter, NewsletterSending, NewsletterItem
from coop_cms.settings import get_article_class, get_newsletter_templates
from coop_cms.widgets import ChosenSelectMultiple


class NewsletterItemAdminForm(forms.ModelForm):
    """admin form for NewsletterItem"""

    def __init__(self, *args, **kwargs):
        super(NewsletterItemAdminForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.item = kwargs.get('instance', None)
        article_choices = [(a.id, '{0}'.format(a)) for a in get_article_class().objects.all()]
        self.fields['object_id'] = forms.ChoiceField(
            choices=article_choices, required=True, help_text=_("Select an article")
        )
        self.fields['content_type'].required = False
        self.fields['content_type'].widget = forms.HiddenInput()

    def clean_content_type(self):
        """validation"""
        return ContentType.objects.get_for_model(get_article_class())


class NewsletterSettingsForm(forms.ModelForm):
    """Newsletter creation form"""

    class Meta:
        model = Newsletter
        fields = ('subject', 'template', 'newsletter_date', 'items', 'site')

    class Media:
        css = {
            'all': ('chosen/chosen.css', ),
        }
        js = (
            'chosen/chosen.jquery.js',
        )

    def __init__(self, user, *args, **kwargs):
        super(NewsletterSettingsForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        tpl_choices = get_newsletter_templates(None, user)
        if tpl_choices:
            self.fields["template"] = forms.ChoiceField(choices=tpl_choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["subject"].widget = forms.TextInput(attrs={'size': 30})
        self.fields["items"].widget.attrs["class"] = "chosen-select"
        choices = list(self.fields['items'].choices)
        sites_choices = []
        current_site = Site.objects.get_current()
        for choice in choices:
            obj_id = choice[0]
            obj = NewsletterItem.objects.get(id=obj_id)
            try:
                has_sites = getattr(obj.content_object, 'sites', None)
            except AttributeError:
                has_sites = False
            if has_sites:
                if current_site in obj.content_object.sites.all():
                    sites_choices.append(choice)
            else:
                sites_choices.append(choice)
        self.fields['items'].choices = sites_choices
        self.fields['items'].widget = ChosenSelectMultiple(
            choices=self.fields['items'].choices, force_template=True
        )

    def clean_items(self):
        """check items"""
        items = self.cleaned_data["items"]
        choice_ids = [choice[0] for choice in self.fields['items'].choices]
        for item in items:
            if item.id not in choice_ids:
                raise ValidationError(_("Invalid choice"))
        return items


class PublishArticleForm(forms.ModelForm):
    """Publish article form"""
    class Meta:
        model = get_article_class()
        fields = ('publication',)
        widgets = {
            'publication': forms.HiddenInput(),
        }


class NewsletterForm(InlineHtmlEditableModelForm):
    """form for newsletter edition"""

    class Meta:
        model = Newsletter
        fields = ('subject', 'content', )


class NewsletterSchedulingForm(floppyforms.ModelForm):
    """Newsletter scheduling"""
    class Meta:
        model = NewsletterSending
        fields = ('scheduling_dt',)

    def clean_scheduling_dt(self):
        """validation"""
        sch_dt = self.cleaned_data['scheduling_dt']

        if not sch_dt:
            raise ValidationError(_("This field is required"))

        if sch_dt < dt_now():
            raise ValidationError(_("The scheduling date must be in future"))

        return sch_dt


class NewsletterTemplateForm(forms.Form):
    """Newsletter template"""

    def __init__(self, newsletter, user, *args, **kwargs):
        super(NewsletterTemplateForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        choices = get_newsletter_templates(newsletter, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["template"].initial = newsletter.template
        

class NewsletterAdminForm(forms.ModelForm):
    """newsletter admin form"""
    def __init__(self, *args, **kwargs):
        super(NewsletterAdminForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.newsletter = kwargs.get('instance', None)
        choices = get_newsletter_templates(self.newsletter, getattr(self, "current_user", None))
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["items"].widget.attrs["class"] = "chosen-select"

    class Meta:
        model = Newsletter
        fields = ('subject', 'content', 'template', 'source_url', 'items', 'newsletter_date', 'site')
        widgets = {}

    class Media:
        css = {
            'all': ('css/admin-tricks.css', 'chosen/chosen.css', ),
        }
        js = (
            'chosen/chosen.jquery.js',
        )

        
class NewsletterHandleRecipients(BsForm):
    email_help_text = ugettext_lazy("Enter another address to send to someone who is not in the list")
    email_label = ugettext_lazy("Email")

    emails = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(), required=False,
        label=_(ugettext_lazy('Emails')), help_text=ugettext_lazy('Check the address if you want to send it the test'),
        choices=[]
    )
    additional_email1 = forms.EmailField(required=False, label=email_label, help_text=email_help_text)
    additional_email2 = forms.EmailField(required=False, label=email_label, help_text=email_help_text)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for elt in getattr(settings, 'COOP_CMS_TEST_EMAILS', []):
            if isinstance(elt, str):
                choices.append((elt, elt))
            else:
                # tuple or list
                choices.append(elt)
        self.fields['emails'].choices = choices

    def clean(self):
        super().clean()
        emails = self.cleaned_data['emails']
        additional_email1 = self.cleaned_data['additional_email1']
        additional_email2 = self.cleaned_data['additional_email2']
        if not emails and not additional_email1 and not additional_email2:
            raise forms.ValidationError(_('Please select or enter at least one email'))
