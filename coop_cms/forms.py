# -*- coding: utf-8 -*-
"""forms"""

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.timezone import now as dt_now
from django.utils.translation import ugettext as _

import floppyforms

from djaloha.widgets import AlohaInput

from coop_cms.models import (
    NavType, NavNode, Newsletter, NewsletterSending, Link, Document, Fragment, FragmentType,
    BaseArticle, MediaFilter, ImageSize, NewsletterItem
)
from coop_cms.settings import (
    get_navigable_content_types, get_article_class, get_article_templates, get_newsletter_templates, get_navtree_class,
    is_localized, can_rewrite_url, is_multi_site
)
from coop_cms.utils import dehtml
from coop_cms.widgets import ImageEdit, ChosenSelectMultiple, ReadOnlyInput


class HidableMultipleChoiceField(floppyforms.MultipleChoiceField):
    """
    The MultipleChoiceField doesn't return an <input type="hidden"> when hidden but an empty string
    Overload this field to restore an <input type="hidden">
    """
    hidden_widget = floppyforms.HiddenInput


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
                    _(u"Invalid rule for this content type: The object class doesn't have a get_label method")
                )
        return rule

    class Meta:
        model = NavType
        fields = ('content_type', 'search_field', 'label_rule')


class AlohaEditableModelForm(floppyforms.ModelForm):
    """Base class for form with Aloha editor fields"""

    def __init__(self, *args, **kwargs):
        super(AlohaEditableModelForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        for field_name in self.Meta.fields:
            no_aloha_widgets = getattr(self.Meta, 'no_aloha_widgets', ())
            if not field_name in no_aloha_widgets: 
                self.fields[field_name].widget = AlohaInput()

    class Media:
        css = {
            'all': ('css/colorbox.css?v=2', ),
        }
        js = (
            'js/jquery.form.js',
            'js/jquery.pageslide.js',
            'js/jquery.colorbox-min.js?v=2',
            'js/colorbox.coop.js?v=2',
        )


class ArticleForm(AlohaEditableModelForm):
    """frontend edition of an article"""

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.article = kwargs.get('instance', None)
        self.set_logo_size()
        if getattr(settings, 'COOP_CMS_TITLE_OPTIONAL', False):
            #Optional title : make possible to remove the title from a template
            self.fields['title'].required = False

    class Meta:
        model = get_article_class()
        fields = ('title', 'subtitle', 'content', 'logo')
        no_aloha_widgets = ('logo',)

    def set_logo_size(self, logo_size=None, logo_crop=None):
        """change logo size"""
        if self.fields.has_key('logo'):
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
                #if the title is optional and nothing is set
                #We do not modify it when saving
                return self.article.title
        else:
            title = self.cleaned_data['title'].strip()
            if title[-4:].lower() == '<br>':
                title = title[:-4]
            if not title:
                raise ValidationError(_(u"Title can not be empty"))
        return title


def get_node_choices():
    """used for node selection in article settings form"""
    prefix = "--"
    choices = [(None, _(u'<not in navigation>'))]
    for tree in get_navtree_class().objects.all():
        choices.append((-tree.id, tree.name))
        for root_node in NavNode.objects.filter(tree=tree, parent__isnull=True).order_by('ordering'):
            for (progeny, level) in root_node.get_progeny():
                choices.append((progeny.id, prefix*(level+1)+progeny.label))
    return choices


def get_navigation_parent_help_text():
    """help text"""
    return get_article_class().navigation_parent.__doc__


class NewsletterItemAdminForm(forms.ModelForm):
    """admin form for NewsletterItem"""

    def __init__(self, *args, **kwargs):
        super(NewsletterItemAdminForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.item = kwargs.get('instance', None)
        article_choices = [(a.id, unicode(a)) for a in get_article_class().objects.all()]
        self.fields['object_id'] = forms.ChoiceField(
            choices=article_choices, required=True, help_text=_(u"Select an article")
        )
        self.fields['content_type'].required = False
        self.fields['content_type'].widget = forms.HiddenInput()

    def clean_content_type(self):
        """validation"""
        return ContentType.objects.get_for_model(get_article_class())


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


class ArticleAdminForm(forms.ModelForm):
    """admin form for article"""

    def __init__(self, *args, **kwargs):
        super(ArticleAdminForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        self.article = kwargs.get('instance', None)
        templates = get_article_templates(self.article, getattr(self, "current_user", None))
        if templates:
            self.fields['template'].widget = forms.Select(choices=templates)
        
        self.slug_fields = []
        if is_localized():
            for lang_and_name in settings.LANGUAGES:
                self.slug_fields.append('slug_'+lang_and_name[0])
        else:
            self.slug_fields = ['slug']
        
        can_change_article_slug = can_rewrite_url()
        
        if not can_change_article_slug:
            can_change_article_slug = (self.article.publication != BaseArticle.PUBLISHED) if self.article else True
        
        for slug_field in self.slug_fields:
            if not can_change_article_slug:
                self.fields[slug_field].widget = ReadOnlyInput()

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


class MediaBaseAddMixin(object):

    def __init__(self, *args, **kwargs):
        super(MediaBaseAddMixin, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        #Media filters
        queryset1 = MediaFilter.objects.all()
        if queryset1.count():
            self.fields['filters'].choices = [(x.id, x.name) for x in queryset1]
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
            attrs={'size': '35', 'placeholder': _(u'Optional description'), }
        ),
        label=_('Description'),
    )
    filters = HidableMultipleChoiceField(
        required=False, label=_(u"Filters"), help_text=_(u"Choose between tags to find images more easily")
    )
    size = floppyforms.ChoiceField(
        required=False, label=_(u"Size"), help_text=_(u"Define a size if you want to resize the image")
    )

    def __init__(self, *args, **kwargs):
        super(AddImageForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        img_size_queryset = ImageSize.objects.all()
        if img_size_queryset.count():
            self.fields['size'].choices = [
                (u'', u'')
            ] + [
                (img_size.id, unicode(img_size)) for img_size in img_size_queryset
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
            raise ValidationError(_(u"Invalid choice"))


class AddDocForm(MediaBaseAddMixin, forms.ModelForm):
    """add document form"""

    filters = floppyforms.MultipleChoiceField(
        required=False, label=_(u"Filters"), help_text=_(u"Choose between tags to find images more easily")
    )

    class Meta:
        model = Document
        fields = ('file', 'name', 'is_private', 'category')


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

        if 'sites' in self.fields:
            self.fields['sites'].initial = [Site.objects.get_current()]
            if not is_multi_site():
                self.fields['sites'].widget = forms.MultipleHiddenInput()

    def clean_site(self):
        """check that the current site is selected"""
        sites = self.cleaned_data['sites']
        if Site.objects.get_current() not in sites:
            raise ValidationError(_(u"It is recommended to keep the current site."))
        return sites


class NewLinkForm(WithNavigationModelForm):
    """New link form"""
    class Meta:
        model = Link
        fields = ('title', 'url',)
    

class NewsletterSettingsForm(forms.ModelForm):
    """Newsletter creation form"""

    class Meta:
        model = Newsletter
        fields = ('subject', 'template', 'items')

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
            if getattr(obj.content_object, 'sites', None):
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
                raise ValidationError(_(u"Invalid choice"))
        return items


class PublishArticleForm(forms.ModelForm):
    """Publish article form"""
    class Meta:
        model = get_article_class()
        fields = ('publication',)
        widgets = {
            'publication': forms.HiddenInput(),
        }


class NewsletterForm(AlohaEditableModelForm):
    """form for newsletter edition"""

    class Meta:
        model = Newsletter
        fields = ('content',)


class NewsletterSchedulingForm(floppyforms.ModelForm):
    """Newsletter scheduling"""
    class Meta:
        model = NewsletterSending
        fields = ('scheduling_dt',)

    def clean_scheduling_dt(self):
        """validation"""
        sch_dt = self.cleaned_data['scheduling_dt']

        if not sch_dt:
            raise ValidationError(_(u"This field is required"))

        if sch_dt < dt_now():
            raise ValidationError(_(u"The scheduling date must be in future"))

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
        fields = ('subject', 'content', 'template', 'source_url', 'items')
        widgets = {}

    class Media:
        css = {
            'all': ('css/admin-tricks.css', 'chosen/chosen.css', ),
        }
        js = (
            'chosen/chosen.jquery.js',
        )


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
