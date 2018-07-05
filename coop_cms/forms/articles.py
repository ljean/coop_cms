# -*- coding: utf-8 -*-
"""forms"""

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from coop_cms.forms.base import InlineHtmlEditableModelForm
from coop_cms.forms.navigation import WithNavigationModelForm
from coop_cms.models import BaseArticle
from coop_cms.settings import (
    get_article_class, get_article_templates, is_localized, can_rewrite_url, is_multi_site
)
from coop_cms.utils import dehtml
from coop_cms.widgets import ImageEdit, ReadOnlyInput


class ArticleForm(InlineHtmlEditableModelForm):
    """frontend edition of an article"""

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002

        self.article = kwargs.get('instance', None)
        self.set_logo_size()
        if getattr(settings, 'COOP_CMS_TITLE_OPTIONAL', False):
            # Optional title : make possible to remove the title from a template
            self.fields['title'].required = False

    class Meta:
        model = get_article_class()
        fields = ('title', 'subtitle', 'content', 'logo')
        no_inline_html_widgets = ('logo',)

    def set_logo_size(self, logo_size=None, logo_crop=None):
        """change logo size"""
        if 'logo' in self.fields:
            thumbnail_src = self.logo_thumbnail(logo_size, logo_crop)
            update_url = reverse('coop_cms_update_logo', args=[self.article.id])
            self.fields['logo'].widget = ImageEdit(
                update_url,
                thumbnail_src.url if thumbnail_src else '',
                attrs={"class": "resizable"}
            )

    def logo_thumbnail(self, logo_size=None, logo_crop=None):
        """transform logo into thumbnail"""
        if self.article:
            return self.article.logo_thumbnail(True, logo_size=logo_size, logo_crop=logo_crop)

    def clean_title(self):
        """article title validation"""
        if getattr(settings, 'COOP_CMS_TITLE_OPTIONAL', False):
            title = self.cleaned_data['title']
            if not title and self.article:
                # if the title is optional and nothing is set
                # We do not modify it when saving
                return self.article.title
        else:
            title = self.cleaned_data['title'].strip()
            if title[-4:].lower() == '<br>':
                title = title[:-4]
            if not title:
                raise ValidationError(_("Title can not be empty"))
        return title


class BaseArticleAdminForm(forms.ModelForm):
    """base form for article admin"""

    def __init__(self, *args, **kwargs):
        super(BaseArticleAdminForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.article = kwargs.get('instance', None)
        templates = get_article_templates(self.article, getattr(self, "current_user", None))
        if templates:
            self.fields['template'].widget = forms.Select(choices=templates)

        self.slug_fields = []
        if is_localized():
            for lang_and_name in settings.LANGUAGES:
                from modeltranslation.utils import build_localized_fieldname
                field_name = build_localized_fieldname('slug', lang_and_name[0])
                self.slug_fields.append(field_name)
        else:
            self.slug_fields = ['slug']

        can_change_article_slug = can_rewrite_url()

        if not can_change_article_slug:
            can_change_article_slug = (self.article.publication != BaseArticle.PUBLISHED) if self.article else True

        for slug_field in self.slug_fields:
            if not can_change_article_slug:
                self.fields[slug_field].widget = ReadOnlyInput()


class ArticleAdminForm(BaseArticleAdminForm):
    """admin form for article"""

    class Meta:
        model = get_article_class()
        fields = (
            'slug', 'title', 'subtitle', 'content', 'template', 'publication', 'logo', 'temp_logo',
            'summary', 'category', 'in_newsletter', 'homepage_for_site', 'headline', 'publication_date', 'sites',
            'login_required',
        )
        widgets = {
            'title': forms.TextInput(attrs={'size': 100})
        }


class ArticleTemplateForm(forms.Form):
    """article template form"""

    def __init__(self, article, user, *args, **kwargs):
        super(ArticleTemplateForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        choices = get_article_templates(article, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["template"].initial = article.template


class ArticleLogoForm(forms.Form):
    """article logo form"""
    image = forms.ImageField(required=True, label=_('Logo'),)


class ArticleSettingsForm(WithNavigationModelForm):
    """article settings"""
    class Meta:
        model = get_article_class()
        fields = (
            'template', 'category', 'publication', 'publication_date', 'headline', 'in_newsletter', 'summary', 'sites',
            'login_required',
        )
        widgets = {
            'sites': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, user, *args, **kwargs):
        article = kwargs['instance']

        try:
            initials = kwargs['initial']
        except KeyError:
            initials = {}
        summary = article.summary
        if not summary:
            summary = dehtml(article.content)[:400]
        initials.update({'summary': summary})
        initials.update({'publication_date': article.publication_date.strftime("%Y-%m-%d %H:%M:%S")})
        
        kwargs['initial'] = initials
        super(ArticleSettingsForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002

        self.fields['category'].queryset = self.fields['category'].queryset.filter(sites=settings.SITE_ID)

        choices = get_article_templates(article, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()

        if 'sites' in self.fields and not is_multi_site():
            self.fields['sites'].widget = forms.MultipleHiddenInput()


class NewArticleForm(WithNavigationModelForm):
    """New article form"""
    class Meta:
        model = get_article_class()
        fields = (
            'title', 'template', 'category', 'headline', 'publication', 'in_newsletter', 'sites', 'login_required',
        )
        widgets = {
            'sites': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, user, *args, **kwargs):
        super(NewArticleForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        choices = get_article_templates(None, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["title"].required = True
        self.fields["title"].widget = forms.TextInput(attrs={'size': 30})

        self.fields['category'].queryset = self.fields['category'].queryset.filter(sites=settings.SITE_ID)

        if 'sites' in self.fields:
            self.fields['sites'].initial = self.get_initials('sites')
            if not is_multi_site():
                self.fields['sites'].widget = forms.MultipleHiddenInput()

    def get_initials(self, field_name):
        """return the initial values"""
        if field_name == 'sites':
            return [Site.objects.get_current()]

    def clean_site(self):
        """check that the current site is selected"""
        sites = self.cleaned_data['sites']
        if Site.objects.get_current() not in sites:
            raise ValidationError(_("It is recommended to keep the current site."))
        return sites


class PublishArticleForm(forms.ModelForm):
    """Publish article form"""
    class Meta:
        model = get_article_class()
        fields = ('publication',)
        widgets = {
            'publication': forms.HiddenInput(),
        }
