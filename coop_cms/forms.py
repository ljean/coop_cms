from django import forms
from coop_cms.models import NavType, NavNode, Newsletter, NewsletterSending, Link, Document, Fragment, BaseArticle
from django.contrib.contenttypes.models import ContentType
from settings import get_navigable_content_types
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from djaloha.widgets import AlohaInput
import floppyforms
import re
from django.conf import settings
from coop_cms.settings import get_article_class, get_article_templates, get_newsletter_templates, get_navtree_class
from coop_cms.widgets import ImageEdit
from django.core.urlresolvers import reverse
from coop_cms.utils import dehtml
from datetime import datetime
from django.utils.timezone import now as dt_now
from coop_cms.widgets import ChosenSelectMultiple, ReadOnlyInput
from settings import is_localized, can_rewrite_url
from django.contrib.auth.models import Permission

class NavTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NavTypeForm, self).__init__(*args, **kwargs)
        self.fields['content_type'].widget = forms.Select(choices=get_navigable_content_types())

    def clean_label_rule(self):
        rule = self.cleaned_data['label_rule']
        if rule == NavType.LABEL_USE_GET_LABEL:
            ct = self.cleaned_data['content_type']
            if not 'get_label' in dir(ct.model_class()):
                raise ValidationError(_(u"Invalid rule for this content type: The object class doesn't have a get_label method"))
        return rule

    class Meta:
        model = NavType

class AlohaEditableModelForm(floppyforms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AlohaEditableModelForm, self).__init__(*args, **kwargs)
        for field_name in self.Meta.fields:
            no_aloha_widgets = getattr(self.Meta, 'no_aloha_widgets', ())
            if not field_name in no_aloha_widgets: 
                self.fields[field_name].widget = AlohaInput()

    class Media:
        css = {
            'all': ('css/colorbox.css?v=2', ),
        }
        js = ('js/jquery.form.js', 'js/jquery.pageslide.js', 'js/jquery.colorbox-min.js?v=2', 'js/colorbox.coop.js?v=2')

class ArticleForm(AlohaEditableModelForm):

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
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
        thumbnail_src = self.logo_thumbnail(logo_size, logo_crop)
        update_url = reverse('coop_cms_update_logo', args=[self.article.id])
        self.fields['logo'].widget = ImageEdit(update_url,
            thumbnail_src.url if thumbnail_src else '',
            attrs={"class": "resizable"})

    def logo_thumbnail(self, logo_size=None, logo_crop=None):
        if self.article:
            return self.article.logo_thumbnail(True, logo_size=logo_size, logo_crop=logo_crop)

    def clean_title(self):
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
    prefix = "--"
    #choices = [(None, _(u'<not in navigation>')), (0, _(u'<root node>'))]
    #for root_node in NavNode.objects.filter(parent__isnull=True).order_by('ordering'):
    #    for (progeny, level) in root_node.get_progeny():
    #        choices.append((progeny.id, prefix*level+progeny.label))
    #return choices
    choices = [(None, _(u'<not in navigation>'))]
    for tree in get_navtree_class().objects.all():
        choices.append((-tree.id, tree.name))
        for root_node in NavNode.objects.filter(tree=tree, parent__isnull=True).order_by('ordering'):
            for (progeny, level) in root_node.get_progeny():
                choices.append((progeny.id, prefix*(level+1)+progeny.label))
    return choices

def get_navigation_parent_help_text():
    return get_article_class().navigation_parent.__doc__

class NewsletterItemAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewsletterItemAdminForm, self).__init__(*args, **kwargs)
        self.item = kwargs.get('instance', None)
        article_choices = [(a.id, unicode(a)) for a in get_article_class().objects.all()]
        self.fields['object_id'] = forms.ChoiceField(
           choices=article_choices, required=True, help_text=_(u"Select an article")
        )
        self.fields['content_type'].required = False
        self.fields['content_type'].widget = forms.HiddenInput()

    def clean_content_type(self):
        return ContentType.objects.get_for_model(get_article_class())

class WithNavigationModelForm(forms.ModelForm):
    navigation_parent = forms.ChoiceField()
    
    def __init__(self, *args, **kwargs):
        super(WithNavigationModelForm, self).__init__(*args, **kwargs)
        #self.instance = kwargs.get('instance', None)
        self.fields['navigation_parent'] = forms.ChoiceField(
            choices=get_node_choices(), required=False, help_text=get_navigation_parent_help_text()
        )
        if self.instance:
            self.fields['navigation_parent'].initial = self.instance.navigation_parent

    def clean_navigation_parent(self):
        parent_id = self.cleaned_data['navigation_parent']
        parent_id = int(parent_id) if parent_id != 'None' else None
        return parent_id

    def save(self, commit=True):
        instance = super(WithNavigationModelForm, self).save(commit=False)
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

    def __init__(self, *args, **kwargs):
        super(ArticleAdminForm, self).__init__(*args, **kwargs)
        self.article = kwargs.get('instance', None)
        templates = get_article_templates(self.article, self.current_user)
        if templates:
            self.fields['template'].widget = forms.Select(choices=templates)
        
        Article = get_article_class()
        
        self.slug_fields = []
        if is_localized():
            for (lang, _name) in settings.LANGUAGES:
                self.slug_fields.append('slug_'+lang)
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
        widgets = {
            'title': forms.TextInput(attrs={'size': 100})
        }

class AddImageForm(forms.Form):
    image = forms.ImageField(required=True, label = _('Image'),)
    descr = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'size': '35', 'placeholder': _(u'Optional description'),}),
        label = _('Description'),
    )

class AddDocForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('file', 'name', 'is_private', 'category')

class ArticleTemplateForm(forms.Form):
    def __init__(self, article, user, *args, **kwargs):
        super(ArticleTemplateForm, self).__init__(*args, **kwargs)
        choices = get_article_templates(article, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["template"].initial = article.template


class ArticleLogoForm(forms.Form):
    image = forms.ImageField(required=True, label = _('Logo'),)

class ArticleSettingsForm(WithNavigationModelForm):
    class Meta:
        model = get_article_class()
        fields = ('template', 'category', 'publication', 'publication_date', 'headline', 'in_newsletter', 'summary',)

    def __init__(self, user, *args, **kwargs):
        article = kwargs['instance']

        try:
            initials = kwargs['initial']
        except:
            initials = {}
        summary = article.summary
        if not summary:
            summary = dehtml(article.content)[:400]
        initials.update({'summary': summary})
        initials.update({'publication_date': article.publication_date.strftime("%Y-%m-%d %H:%M:%S")})
        
        kwargs['initial'] = initials
        super(ArticleSettingsForm, self).__init__(*args, **kwargs)

        self.fields['category'].queryset = self.fields['category'].queryset.filter(sites=settings.SITE_ID)

        choices = get_article_templates(article, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()

class NewArticleForm(WithNavigationModelForm):
    class Meta:
        model = get_article_class()
        fields = ('title', 'template', 'category', 'headline', 'publication', 'in_newsletter')

    def __init__(self, user, *args, **kwargs):
        super(NewArticleForm, self).__init__(*args, **kwargs)
        choices = get_article_templates(None, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["title"].widget = forms.TextInput(attrs={'size': 30})


class NewLinkForm(WithNavigationModelForm):
    
    class Meta:
        model = Link
        fields = ('title', 'url',)
    

class NewNewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ('subject', 'template', 'items')
        #widgets = {}
        #try:
        #    widgets.update({
        #        'items': ChosenSelectMultiple(),
        #    })
        #except NameError:
        #    print 'NO ChosenSelectMultiple'
        #    pass

    def __init__(self, user, *args, **kwargs):
        super(NewNewsletterForm, self).__init__(*args, **kwargs)
        tpl_choices = get_newsletter_templates(None, user)
        if tpl_choices:
            self.fields["template"] = forms.ChoiceField(choices=tpl_choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["subject"].widget = forms.TextInput(attrs={'size': 30})


class PublishArticleForm(forms.ModelForm):
    class Meta:
        model = get_article_class()
        fields = ('publication',)# 'summary', 'category')
        widgets = {
            'publication': forms.HiddenInput(),
        }

    #def __init__(self, *args, **kwargs):
    #    article = kwargs['instance']
    #    try:
    #        initials = kwargs['initial']
    #    except:
    #        initials = {}
    #    summary = article.summary
    #    if not summary:
    #        summary = dehtml(article.content)[:250]
    #    initials.update({'summary': summary})
    #    kwargs['initial'] = initials
    #    super(PublishArticleForm, self).__init__(*args, **kwargs)

class NewsletterForm(AlohaEditableModelForm):
    class Meta:
        model = Newsletter
        fields = ('content',)
    
#class NewsletterForm(floppyforms.ModelForm):
#
#    class Meta:
#        model = Newsletter
#        fields = ('content',)
#        widgets = {
#            'content': AlohaInput(text_color_plugin=False),
#        }
#
#    class Media:
#        css = {
#            'all': ('css/colorbox.css', ),
#        }
#        js = ('js/jquery.form.js', 'js/jquery.pageslide.js', 'js/jquery.colorbox-min.js', 'js/colorbox.coop.js')
#

class NewsletterSchedulingForm(floppyforms.ModelForm):
    class Meta:
        model = NewsletterSending
        fields = ('scheduling_dt',)

    def clean_scheduling_dt(self):
        sch_dt = self.cleaned_data['scheduling_dt']

        if not sch_dt:
            raise ValidationError(_(u"This field is required"))

        if sch_dt < dt_now():
            raise ValidationError(_(u"The scheduling date must be in future"))

        return sch_dt

class NewsletterTemplateForm(forms.Form):

    def __init__(self, newsletter, user, *args, **kwargs):
        super(NewsletterTemplateForm, self).__init__(*args, **kwargs)
        choices = get_newsletter_templates(newsletter, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["template"].initial = newsletter.template
        
        

class NewsletterAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NewsletterAdminForm, self).__init__(*args, **kwargs)
        self.newsletter = kwargs.get('instance', None)
        choices = get_newsletter_templates(self.newsletter, self.current_user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()

    class Meta:
        model = Newsletter
        fields = ('subject', 'content', 'template', 'source_url', 'items')
        widgets = {}
        try:
            widgets.update({
                'items': ChosenSelectMultiple(),
            })
        except NameError:
            #print 'No ChosenSelectMultiple'
            pass

    class Media:
        css = {
            'all': ('css/admin-tricks.css',),
        }
        js = ()
        
class AddFragmentForm(forms.ModelForm):

    class Meta:
        model = Fragment
        fields = ('type', 'name', 'position', 'filter')
        
    def __init__(self, data=None, *args, **kwargs):
        super(AddFragmentForm, self).__init__(data, *args, **kwargs)
        self.fields['filter'].widget = forms.HiddenInput()
        
class EditFragmentForm(forms.ModelForm):
    delete_me = forms.BooleanField(label=_(u"delete"), required=False)

    class Meta:
        model = Fragment
        fields = ('type', 'filter', 'name', 'css_class', 'position')
        widgets = {
            "type": forms.HiddenInput(),
            "filter": forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        super(EditFragmentForm, self).__init__(*args, **kwargs)
        choices = [('', '')]+[(x, x) for x in self.instance.type.allowed_css_classes.split(',')]
        self.fields['css_class'].widget = forms.Select(choices=choices)
        
    def clean_css_class(self):
        val = self.cleaned_data['css_class']
        if val:
            if not val in self.instance.type.allowed_css_classes.split(','):
                val = u""
        return val
        
    def save(self, *args, **kwargs):
        if self.cleaned_data['delete_me']:
            self.instance.delete()
            return None
        return super(EditFragmentForm, self).save(*args, **kwargs)
    