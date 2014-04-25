# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
import models
from forms import NavTypeForm, ArticleAdminForm, NewsletterItemAdminForm, NewsletterAdminForm
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from coop_cms.settings import get_article_class, get_navtree_class
from django.conf import settings
from settings import is_localized, can_rewrite_url

if 'modeltranslation' in settings.INSTALLED_APPS:
    from modeltranslation.admin import TranslationAdmin
    BaseAdminClass = TranslationAdmin
else:
    BaseAdminClass = admin.ModelAdmin


class NavNodeAdmin(admin.ModelAdmin):
    list_display = ["label", 'parent', 'ordering', 'in_navigation', 'content_type', 'object_id']

admin.site.register(models.NavNode, NavNodeAdmin)


class NavTypeAdmin(admin.ModelAdmin):
    form = NavTypeForm

admin.site.register(models.NavType, NavTypeAdmin)


class NavTreeAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'name', 'navtypes_list']
    list_editable = ['name']
    list_filters = ['id']

    def nodes_li(self, tree):
        root_nodes = tree.get_root_nodes()
        nodes_li = u''.join([node.as_jstree() for node in root_nodes])
        return nodes_li

    def navtypes_list(self, tree):
        if tree.types.count() == 0:
            return _(u'All')
        else:
            return u' - '.join([unicode(x) for x in tree.types.all()])
    navtypes_list.short_description = _(u'navigable types')

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        tree = models.get_navtree_class().objects.get(id=object_id)
        extra_context['navtree'] = tree
        extra_context['navtree_nodes'] = self.nodes_li(tree)
        return super(NavTreeAdmin, self).change_view(request, object_id,
            extra_context=extra_context)

admin.site.register(get_navtree_class(), NavTreeAdmin)


class ArticleAdmin(BaseAdminClass):
    form = ArticleAdminForm
    list_display = ['slug', 'title', 'category', 'template_name', 'publication', 'headline', 'in_newsletter', 'modified']
    list_editable = ['publication', 'headline', 'in_newsletter', 'category']
    readonly_fields = ['created', 'modified', 'is_homepage']
    list_filter = ['publication', 'headline', 'in_newsletter', 'sites', 'homepage_for_site', 'category', 'template']
    date_hierarchy = 'publication_date'
    fieldsets = (
        #(_('Navigation'), {'fields': ('navigation_parent',)}),
        (_(u'General'), {'fields': ('slug', 'title', 'subtitle', 'publication', )}),
        (_(u'Settings'), {'fields': ('sites', 'template', 'category', 'headline', 'is_homepage', 'logo', 'in_newsletter')}),
        (_(u'Advanced'), {'fields': ('publication_date', 'homepage_for_site', 'created', 'modified')}),
        (_(u'Content'), {'fields': ('content','summary',)}),
        (_(u'Debug'), {'fields': ('temp_logo',)}),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticleAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form
    
admin.site.register(get_article_class(), ArticleAdmin)

admin.site.register(models.Link)
admin.site.register(models.Document)
admin.site.register(models.Image)
admin.site.register(models.PieceOfHtml)
admin.site.register(models.NewsletterSending)
admin.site.register(models.FragmentType)
admin.site.register(models.FragmentFilter)

class FragmentAdmin(BaseAdminClass):
    pass
    list_display = ['name', 'position', 'type', 'filter', 'css_class']
    list_filter = ['type', 'filter', 'css_class']

admin.site.register(models.Fragment, FragmentAdmin)


class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'ordering', 'in_rss']
    list_editable = ['ordering', 'in_rss']
admin.site.register(models.ArticleCategory, ArticleCategoryAdmin)

class NewsletterItemAdmin(admin.ModelAdmin):
    form = NewsletterItemAdminForm
    list_display = ['content_type', 'content_object', 'ordering']
    list_editable = ['ordering']
    fieldsets = (
        (_('Article'), {'fields': ('object_id', 'content_type', 'ordering')}),
    )

admin.site.register(models.NewsletterItem, NewsletterItemAdmin)


class NewsletterAdmin(admin.ModelAdmin):
    form = NewsletterAdminForm
    raw_id_fields = ['items']
    list_display = ['subject', 'template', 'source_url']

    def get_form(self, request, obj=None, **kwargs):
        form = super(NewsletterAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

admin.site.register(models.Newsletter, NewsletterAdmin)

class AliasAdmin(admin.ModelAdmin):
    list_display = ['path', 'redirect_url']
    list_editable = ['redirect_url']
admin.site.register(models.Alias, AliasAdmin)
