# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.template.loader import get_template
from django.template import Context
from django_extensions.db.models import TimeStampedModel, AutoSlugField
from django.conf import settings
from sorl.thumbnail import default as sorl_thumbnail
import os, os.path, shutil
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Max
from django.utils.html import escape
from django.core.exceptions import ValidationError
# from html_field.db.models import HTMLField
# from html_field import html_cleaner
from coop_cms.settings import get_article_class, get_article_logo_size, get_newsletter_item_classes, get_article_logo_crop
from coop_cms.settings import get_navtree_class, is_localized, COOP_CMS_NAVTREE_CLASS, get_article_templates
from coop_cms.settings import get_default_logo, is_requestprovider_installed
from coop_cms.utils import dehtml
from django.contrib.staticfiles import finders
from django.core.files import File
from django.db.models.signals import pre_delete, post_save
from django.template.defaultfilters import slugify, escape
from datetime import datetime
from django.utils import translation
import urlparse
from sorl.thumbnail import default
from django.contrib.sites.models import Site
ADMIN_THUMBS_SIZE = '60x60'


def get_object_label(content_type, object):
    """
    returns the label used in navigation according to the configured rule
    """
    if not object:
        return _(u"Node")
    try:
        nt = NavType.objects.get(content_type=content_type)
        if nt.label_rule == NavType.LABEL_USE_SEARCH_FIELD:
            label = getattr(object, nt.search_field)
        elif nt.label_rule == NavType.LABEL_USE_GET_LABEL:
            label = object.get_label()
        else:
            label = unicode(object)
    except NavType.DoesNotExist:
        label = unicode(object)
    return label

def set_node_ordering(node, tree, parent):
    if parent:
        node.parent = parent
        sibling_nodes = NavNode.objects.filter(tree=tree, parent=node.parent)
    else:
        node.parent = None
        sibling_nodes = NavNode.objects.filter(tree=tree, parent__isnull=True)
    max_ordering = sibling_nodes.aggregate(max_ordering=Max('ordering'))['max_ordering'] or 0
    node.ordering = max_ordering + 1

def create_navigation_node(content_type, object, tree, parent):
    node = NavNode(tree=tree, label=get_object_label(content_type, object))
    #add it as last child of the selected node
    set_node_ordering(node, tree, parent)
    #associate with a content object
    node.content_type = content_type
    node.object_id = object.id if object else 0
    node.save()
    return node

class NavType(models.Model):
    """Define which ContentTypes can be inserted in the tree as content"""

    LABEL_USE_UNICODE = 0
    LABEL_USE_SEARCH_FIELD = 1
    LABEL_USE_GET_LABEL = 2

    LABEL_RULE_CHOICES = (
        (LABEL_USE_UNICODE, _(u'Use object unicode')),
        (LABEL_USE_SEARCH_FIELD, _(u'Use search field')),
        (LABEL_USE_GET_LABEL, _(u'Use get_label')),
    )

    content_type = models.ForeignKey(ContentType, unique=True, verbose_name=_(u'django model'))
    search_field = models.CharField(max_length=200, blank=True, default="", verbose_name=_(u'search field'))
    label_rule = models.IntegerField(verbose_name=_(u'How to generate the label'),
        choices=LABEL_RULE_CHOICES, default=LABEL_USE_UNICODE)

    def __unicode__(self):
        return self.content_type.app_label+'.'+self.content_type.model

    class Meta:
        verbose_name = _(u'navigable type')
        verbose_name_plural = _(u'navigable types')


class NavNode(models.Model):
    """
    A navigation node
    Part of the tree as child of his parent
    Point on a content_object
    """

    tree = models.ForeignKey(COOP_CMS_NAVTREE_CLASS, verbose_name=_("tree"))
    label = models.CharField(max_length=200, verbose_name=_("label"))
    parent = models.ForeignKey("NavNode", blank=True, null=True, default=0, verbose_name=_("parent"))
    ordering = models.PositiveIntegerField(_("ordering"), default=0)

    #generic relation
    content_type = models.ForeignKey(ContentType, verbose_name=_("content_type"), blank=True, null=True)
    object_id = models.PositiveIntegerField(verbose_name=_("object id"), blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    in_navigation = models.BooleanField(_("in navigation"), default=True)

    def get_absolute_url(self):
        try:
            if self.content_object:
                return self.content_object.get_absolute_url()
        except AttributeError:
            pass
        return None
    
    def is_active_node(self):
        url = self.get_absolute_url()
        if url and is_requestprovider_installed():
            from gadjo.requestprovider.signals import get_request
            try:
                http_request = get_request()
                return http_request and http_request.path == url
            except IndexError:
                pass
        return False

    def get_content_name(self):
        return self.content_type.model_class()._meta.verbose_name

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _(u'navigation node')
        verbose_name_plural = _(u'navigation nodes')
        #unique_together = ('content_type', 'object_id')

    def get_children(self, in_navigation=None):
        nodes = NavNode.objects.filter(parent=self).order_by("ordering")
        if in_navigation != None:
            nodes = nodes.filter(in_navigation=in_navigation)
        return nodes

    def has_children(self):
        return self.get_children(True).count()
    
    def get_children_navigation(self):
        return self.get_children(True)

    def get_siblings(self, in_navigation=None):
        nodes = NavNode.objects.filter(parent=self.parent).order_by("ordering")
        if in_navigation != None:
            nodes = nodes.filter(in_navigation=in_navigation)
        return nodes

    def get_progeny(self, level=0):
        progeny = []
        progeny.append((self, level))
        for child in NavNode.objects.filter(parent=self).order_by("ordering"):
            progeny.extend(child.get_progeny(level+1))
        return progeny

    def as_jstree(self):
        url = self.get_absolute_url()
        label = escape(self.label)
        if url == None:
            li_content = u'<a>{0}</a>'.format(label)
        else:
            li_content = u'<a href="{0}">{1}</a>'.format(url, label)

        children_li = [child.as_jstree() for child in self.get_children()]

        return u'<li id="node_{0}" rel={3}>{1}<ul>{2}</ul></li>'.format(
            self.id, li_content, u''.join(children_li), "in_nav" if self.in_navigation else "out_nav"
        )

    def _get_li_content(self, li_template):
        if li_template:
            t = li_template if hasattr(li_template, 'render') else get_template(li_template)
            return t.render(Context({'node': self}))
        else:
            url = self.get_absolute_url()
            if url == None:
                return u'<a>{0}</a>'.format(self.label)
            else:
                return u'<a href="{0}">{1}</a>'.format(url, self.label)

    def _get_ul_format(self, ul_template):
        if ul_template:
            t = ul_template if hasattr(ul_template, 'render') else get_template(ul_template)
            return t.render(Context({'node': self}))
        else:
            return u'<ul>{0}</ul>'

    def _get_li_args(self, li_args):
        if li_args:
            t = li_args if hasattr(li_args, 'render') else get_template(li_args)
            return t.render(Context({'node': self}))
        else:
            return u''
        
    #def render(self, template_name):
    #    t = get_template(template_name)
    #    return t.render(Context({'node': self}))

    def as_navigation(self, li_template=None, css_class="", ul_template=None, li_args=None, active_class="active-node"):
        #Display the node and his children as nested ul and li html tags.
        #li_template is a custom template that can be passed

        if not self.in_navigation:
            return ""

        children_li = [child.as_navigation(li_template, css_class) for child in self.get_children(in_navigation=True)]
        ul_format = self._get_ul_format(ul_template)
        children_html = ul_format.format(u''.join(children_li)) if children_li else ""
        args = self._get_li_args(li_args)
        if args.find("class=")<0:
            css_class = u'class="{0} {1}"'.format(css_class, active_class if self.is_active_node() else "")
        else:
            css_class=""
        return u'<li {0} {1}>{2}{3}</li>'.format(
            css_class, args, self._get_li_content(li_template), children_html)

    def as_breadcrumb(self, li_template=None, css_class=""):
        html = self.parent.as_breadcrumb(li_template) if self.parent else u""
        return html + u'<li class="{0}">{1}</li>'.format(css_class, self._get_li_content(li_template))

    def children_as_navigation(self, li_template=None, css_class=""):
        children_li = [u'<li class="{0}">{1}</li>'.format(css_class, child._get_li_content(li_template))
            for child in self.get_children(in_navigation=True)]
        return  u''.join(children_li)

    def siblings_as_navigation(self, li_template=None, css_class=""):
        siblings_li = [u'<li class="{0}">{1}</li>'.format(css_class, sibling._get_li_content(li_template))
            for sibling in self.get_siblings(in_navigation=True)]
        return  u''.join(siblings_li)

    def check_new_navigation_parent(self, parent_id):
        if parent_id == self.id:
            raise ValidationError(_(u'A node can not be its own parent'))

        if parent_id:
            cur_node = NavNode.objects.get(id=parent_id)
            while cur_node:
                if cur_node.id == self.id:
                    raise ValidationError(_(u'A node can not be child of its own child'))
                cur_node = cur_node.parent


class BaseNavTree(models.Model):
    last_update = models.DateTimeField(auto_now=True)
    name = models.CharField(_(u'name'), max_length=100, db_index=True, unique=True, default='default')
    types = models.ManyToManyField('coop_cms.NavType', blank=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('navigation_tree', args=[self.id])

    def get_root_nodes(self):
        return NavNode.objects.filter(tree=self, parent__isnull=True).order_by("ordering")

    class Meta:
        verbose_name = _(u'Navigation tree')
        verbose_name_plural = _(u'Navigation trees')
        abstract = True

#content_cleaner = html_cleaner.HTMLCleaner(
#    allow_tags=['a', 'img', 'p', 'br', 'b', 'i', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
#        'sup', 'pre', 'ul', 'li', 'ol', 'table', 'th', 'tr', 'td', 'tbody', 'span', 'div',
#        'strong','u','dd','dt','dl','hr','em','font','iframe','object','param','embed'],
#        #iframe is a security risk but needed until we find how to integrate oembed
#    allow_attrs_for_tag={'a': ['href', 'target'], 'img': ['src', 'alt']}
#)
#title_cleaner = html_cleaner.HTMLCleaner(allow_tags=['br','span','em','i','strong','b','font','u'])

class ArticleCategory(models.Model):
    name = models.CharField(_(u'name'), max_length=100)
    slug = AutoSlugField(populate_from='name', max_length=100, unique=True)
    ordering = models.IntegerField(_(u'ordering'), default=0)
    in_rss = models.BooleanField(_(u'in rss'), default=False,
        help_text=_(u"The articles of this category will be listed in the main rss feed"))
    sites = models.ManyToManyField(Site, verbose_name=_(u'site'), default=[settings.SITE_ID])

    def __unicode__(self):
        return self.name
    
    def can_view_category(self, user):
        return True

    def get_absolute_url(self):
        return reverse('coop_cms_articles_category', args=[self.slug])
    
    def get_articles_qs(self):
        return get_article_class().objects.filter(
            category=self, publication=BaseArticle.PUBLISHED).order_by('publication_date')

    class Meta:
        verbose_name = _(u'article category')
        verbose_name_plural = _(u'article categories')
        
    def save(self, *args, **kwargs):
        is_new = not bool(self.id)
        ret = super(ArticleCategory, self).save(*args, **kwargs)
        
        if is_new:
            site = Site.objects.get(id=settings.SITE_ID)
            self.sites.add(site)
            ret = super(ArticleCategory, self).save()

class BaseNavigable(TimeStampedModel):

    class Meta:
        abstract = True

    def _get_navigation_parent(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        nodes = NavNode.objects.filter(object_id=self.id, content_type=ct)
        if nodes.count():
            node = nodes[0]
            if node.parent:
                return node.parent.id
            else:
                return -node.tree.id
        else:
            return None

    def _set_navigation_parent(self, value):
        ct = ContentType.objects.get_for_model(self.__class__)
        if value != None:
            if value < 0:
                tree_id = -value
                tree = get_navtree_class().objects.get(id=tree_id)
                parent = None
            else:
                parent = NavNode.objects.get(id=value)
                tree = parent.tree

            create_navigation_node(ct, self, tree, parent)

    navigation_parent = property(_get_navigation_parent, _set_navigation_parent,
        doc=_("set the parent in navigation."))

    def save(self, do_not_create_nav=False, *args, **kwargs):
        ret = super(BaseNavigable, self).save(*args, **kwargs)
        if not do_not_create_nav:
            parent_id = getattr(self, '_navigation_parent', None)
            if parent_id != None:
                self.navigation_parent = parent_id
        return ret

class BaseArticle(BaseNavigable):
    """An article : static page, blog item, ..."""

    DRAFT = 0
    PUBLISHED = 1

    PUBLICATION_STATUS = (
        (DRAFT, _(u'Draft')),
        (PUBLISHED, _(u'Published')),
    )

    def get_logo_folder(self, filename):
        try:
            img_root = settings.CMS_ARTICLE_LOGO_FOLDER
        except AttributeError:
            img_root = 'cms_logos'
        basename = os.path.basename(filename)   
        return u'{0}/{1}/{2}'.format(img_root, self.id, basename)
        

    #slug = AutoSlugField(populate_from='title', max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True, db_index=True, blank=False)
    #title = HTMLField(title_cleaner, verbose_name=_(u'title'), default=_('Page title'))
    #content = HTMLField(content_cleaner, verbose_name=_(u'content'), default=_('Page content'))
    title = models.TextField(_(u'title'), default='', blank=True)
    subtitle = models.TextField(_(u'subtitle'), default='', blank=True)
    content = models.TextField(_(u'content'), default='', blank=True)
    publication = models.IntegerField(_(u'publication'), choices=PUBLICATION_STATUS, default=PUBLISHED)
    template = models.CharField(_(u'template'), max_length=200, default='', blank=True)
    logo = models.ImageField(upload_to=get_logo_folder, blank=True, null=True, default='')
    temp_logo = models.ImageField(upload_to=get_logo_folder, blank=True, null=True, default='')
    summary = models.TextField(_(u'Summary'), blank=True, default='')
    category = models.ForeignKey(ArticleCategory, verbose_name=_(u'Category'), blank=True, null=True, default=None, related_name="%(app_label)s_%(class)s_rel")
    in_newsletter = models.BooleanField(_(u'In newsletter'), default=True, help_text=_(u'Make this article available for newsletters.'))
    homepage_for_site = models.ForeignKey(Site, verbose_name=_(u'Homepage for site'), blank=True, null=True, default=None, related_name="homepage_article")
    headline = models.BooleanField(_(u"Headline"), default=False, help_text=_(u'Make this article appear on the home page'))
    publication_date = models.DateTimeField(_(u"Publication date"), default=datetime.now())
    sites = models.ManyToManyField(Site, verbose_name=_(u'site'), default=[settings.SITE_ID])
    
    @property
    def is_homepage(self):
        if self.homepage_for_site:
            return self.homepage_for_site.id == settings.SITE_ID
        return False
    
    def is_draft(self):
        return self.publication == BaseArticle.DRAFT
    
    def next_in_category(self):
        if self.category:
            try:
                return get_article_class().objects.filter(sites__id=settings.SITE_ID, category=self.category,
                    publication=BaseArticle.PUBLISHED,
                    publication_date__gt=self.publication_date).order_by('publication_date')[0]
            except IndexError:
                pass
        
    def previous_in_category(self):
        if self.category:
            try:
                return get_article_class().objects.filter(
                    sites__id=settings.SITE_ID, category=self.category,
                    publication=BaseArticle.PUBLISHED,
                    publication_date__lt=self.publication_date).order_by('-publication_date')[0]
            except IndexError:
                pass

    def logo_thumbnail(self, temp=False, logo_size=None, logo_crop=None):
        logo = self.temp_logo if (temp and self.temp_logo) else self.logo
        size = logo_size or get_article_logo_size(self)
        logo_file = None
        if logo:
            try:
                logo_file = logo.file
            except IOError:
                pass
        if not logo_file:
            logo_file = self._get_default_logo()
        crop = logo_crop or get_article_logo_crop(self)
        try:
            return sorl_thumbnail.backend.get_thumbnail(logo_file, size, crop=crop)
        except Exception, msg:
            print "#### ERR", msg
            return logo_file

    def _get_default_logo(self):
        #copy from static to media in order to use sorl thumbnail without raising a suspicious operation
        filename = get_default_logo()
        media_filename = os.path.normpath(settings.MEDIA_ROOT + '/coop_cms/' + filename)
        if not os.path.exists(media_filename):
            dir = os.path.dirname(media_filename)
            if not os.path.exists(dir):
                os.makedirs(dir)
            static_filename = finders.find(filename)
            shutil.copyfile(static_filename, media_filename)
        return File(open(media_filename, 'r'))

    def logo_list_display(self):
        if self.logo:
            thumb = default.backend.get_thumbnail(self.logo.file, ADMIN_THUMBS_SIZE)
            return '<img width="%s" src="%s" />' % (thumb.width, thumb.url)
        else:
            return _(u"No Image")
    logo_list_display.short_description = _(u"logo")
    logo_list_display.allow_tags = True

    class Meta:
        verbose_name = _(u"article")
        verbose_name_plural = _(u"articles")
        abstract = True

    def __unicode__(self):
        return self.title


    def save(self, *args, **kwargs):
        if hasattr(self, "_cache_slug"): delattr(self, "_cache_slug")
        
        #autoslug localized title for creating locale_slugs
        if (not self.title) and (not self.slug):
            raise Exception(u"coop_cms.Article: slug can not be empty")
            
        if is_localized():
            from modeltranslation.utils import build_localized_fieldname
            for (lang_code, lang_name) in settings.LANGUAGES:
                loc_title_var = build_localized_fieldname('title', lang_code)
                locale_title = getattr(self, loc_title_var, '')
            
                loc_slug_var = build_localized_fieldname('slug', lang_code)
                locale_slug = getattr(self, loc_slug_var, '')
                
                if locale_title and not locale_slug:
                    #slug = self.get_unique_slug(loc_slug_var, locale_title)
                    slug = self.get_unique_slug('slug', locale_title)
                    setattr(self, loc_slug_var, slug)
        else:
            if not self.slug:
                self.slug = self.get_unique_slug('slug', self.title)
        
        is_new = not bool(self.id)
        ret = super(BaseArticle, self).save(*args, **kwargs)
        
        if is_new:
            site = Site.objects.get(id=settings.SITE_ID)
            self.sites.add(site)
            ret = super(BaseArticle, self).save(do_not_create_nav=True)
        
        if self.homepage_for_site and (self.homepage_for_site.id == settings.SITE_ID):
            for a in get_article_class().objects.filter(homepage_for_site__id=settings.SITE_ID).exclude(id=self.id):
                a.homepage_for_site = None
                a.save()
        
        return ret
    
    def get_unique_slug(self, slug_field, title):
        #no html in title
        title = dehtml(title)
        slug = slugify(title)
        next_suffix, origin_slug = 2, slug
        Article = get_article_class()
        slug_exists = True
        while slug_exists:
            #Check that this slug doesn't already exist
            #The slug must be unique for all sites
            if is_localized():
                from modeltranslation.utils import build_localized_fieldname
                slug_fields = []
                for (lang_code, lang_name) in settings.LANGUAGES:
                    loc_slug_var = build_localized_fieldname('slug', lang_code)
                    slug_fields.append(loc_slug_var)
            else:
                slug_fields = ('slug',)
            
            slug_exists = False
            for slug_field in slug_fields:
                try:
                    attrs = {slug_field: slug}
                    if self.id:
                        Article.objects.get(Q(**attrs) & ~Q(id=self.id))
                    else:
                        Article.objects.get(**attrs)
                    #the slug exists in one language: we can not use it, try another one
                    slug_exists = True
                    break
                except Article.DoesNotExist:
                    pass #Ok this slug is not used: break the loop and return
            
            if slug_exists:
                #oups the slug is already used: change it and try again
                next_suffix_len = len(str(next_suffix))
                safe_slug = origin_slug[:(100-next_suffix_len)]
                slug = u"{0}{1}".format(safe_slug, next_suffix)
                next_suffix += 1
        return slug
        
    def template_name(self):
        possible_templates = get_article_templates(self, None)
        for (template, name) in possible_templates:
            if template == self.template:
                return name
        return u"?"

    def get_label(self):
        return self.title

    def _get_slug(self):
        slug = getattr(self, '_cache_slug', None)
        if slug:
            return slug
        slug = self.slug
        if not slug:
            for (l, n) in settings.LANGUAGES:
                key = 'slug_{0}'.format(l)
                slug = getattr(self, key)
                if slug:
                    break
        setattr(self, '_cache_slug', slug)
        return slug

    def get_absolute_url(self):
        return reverse('coop_cms_view_article', args=[self._get_slug()])

    def get_edit_url(self):
        return reverse('coop_cms_edit_article', args=[self._get_slug()])

    def get_cancel_url(self):
        return reverse('coop_cms_cancel_edit_article', args=[self._get_slug()])

    def get_publish_url(self):
        return reverse('coop_cms_publish_article', args=[self._get_slug()])

    def _can_change(self, user):
        ct = ContentType.objects.get_for_model(get_article_class())
        perm = '{0}.change_{1}'.format(ct.app_label, ct.model)
        return user.has_perm(perm)

    def can_view_article(self, user):
        if self.publication != BaseArticle.PUBLISHED:
            return self.can_edit_article(user)
        else:
            return True

    def can_edit_article(self, user):
        return self._can_change(user)

    def can_publish_article(self, user):
        return self._can_change(user)

class Link(BaseNavigable):
    """Link to a given url"""
    title = models.CharField(_(u'Title'), max_length=200, default=_(u"title"))
    url = models.CharField(_(u'URL'), max_length=200)

    def get_absolute_url(self):
        if is_localized():
            scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.url)
            if not scheme:
                #the urls doesn't starts with http://, so it's a url managed by the site
                from localeurl.utils import locale_path
                locale = translation.get_language()                
                return locale_path(self.url, locale)
        return self.url

    def get_label(self):
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.url)
        if scheme:
            return u"{0}{1}".format(netloc, path)
        return self.url

    def __unicode__(self):
        return dehtml(self.title)

    class Meta:
        verbose_name = _(u"link")
        verbose_name_plural = _(u"links")

def get_img_folder(instance, filename):
    try:
        img_root = settings.IMAGE_FOLDER
    except AttributeError:
        img_root = 'img'

    return u'{0}/{1}/{2}'.format(img_root,
        instance.created.strftime('%Y%d%m%H%M%S'), filename)

class Media(TimeStampedModel):
    name = models.CharField(_('name'), max_length=200, blank=True, default='')

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

class Image(Media):
    file = models.ImageField(_('file'), upload_to=get_img_folder)

    def as_thumbnail(self):
        try:
            return sorl_thumbnail.backend.get_thumbnail(self.file.file, "64x64", crop='center')
        except Exception, msg:
            return self.file
        

    def get_absolute_url(self):
        return self.file.url

    class Meta:
        verbose_name = _(u'image')
        verbose_name_plural = _(u'images')

class Document(Media):
    def get_doc_folder(self, filename):
        if not self.is_private:
            try:
                doc_root = settings.DOCUMENT_FOLDER
            except AttributeError:
                doc_root = 'documents/public'
        else:
            try:
                doc_root = settings.PRIVATE_DOCUMENT_FOLDER
            except AttributeError:
                doc_root = 'documents/private'

        filename = os.path.basename(filename)
        #This is required for x-sendfile
        name, ext = os.path.splitext(filename)
        filename = slugify(name) + ext
        
        return u'{0}/{1}/{2}'.format(doc_root,
            self.created.strftime('%Y%d%m%H%M%S'), filename)

    file = models.FileField(_('file'), upload_to=get_doc_folder)
    is_private = models.BooleanField(_('is private'), default=False,
        help_text=_(u"Check this if you do not want to publish this document to all users"))
    category = models.ForeignKey(ArticleCategory, blank=True, null=True, default=None, verbose_name=_(u'category'))

    def can_download_file(self, user):
        return user.is_authenticated()

    def get_download_url(self):
        if self.is_private:
            return reverse('coop_cms_download_doc', args=[self.id])
        else:
            return self.file.url

    def get_ico_url(self, icotype):
        root, ext = os.path.splitext(self.file.name)
        ext = ext[1:].lower()  # remove leading dot
        if ext in ('pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'png', 'jpg', 'gif', \
                    'ppt', 'pps', 'mp3', 'ogg', 'html', 'rtf', 'zip', 'avi', \
                    'mov', 'mp4', ):
            return settings.STATIC_URL + u'img/filetypes/' + icotype + '/{0}.png'.format(ext)
        else:
            return settings.STATIC_URL + u'img/filetypes/' + icotype + '/default.png'

    def get_block_url(self):
        return self.get_ico_url('bloc')

    def get_fileicon_url(self):
        return self.get_ico_url('icon')

    class Meta:
        verbose_name = _(u'document')
        verbose_name_plural = _(u'documents')

class PieceOfHtml(models.Model):
    div_id = models.CharField(verbose_name=_(u"identifier"), max_length=100, db_index=True)
    #content = HTMLField(content_cleaner, verbose_name=_(u"content"), default="", blank=True)
    content = models.TextField(_(u"content"), default="", blank=True)

    def __unicode__(self):
        return self.div_id

    class Meta:
        verbose_name = _(u'piece of HTML')
        verbose_name_plural = _(u'pieces of HTML')

#delete node when content object is deleted
def remove_from_navigation(sender, instance, **kwargs):
    if hasattr(instance, 'id'):
        try:
            ct = ContentType.objects.get_for_model(instance)
            node = NavNode.objects.get(content_type=ct, object_id=instance.id)
            node.delete()
        except (NavNode.DoesNotExist, ContentType.DoesNotExist):
            pass
pre_delete.connect(remove_from_navigation)

class NewsletterItem(models.Model):
    content_type = models.ForeignKey(ContentType, verbose_name=_("content_type"))
    object_id = models.PositiveIntegerField(verbose_name=_("object id"))
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    ordering = models.IntegerField(verbose_name=_("ordering"), default=0)

    class Meta:
        unique_together = (("content_type", "object_id"),)
        verbose_name = _(u'newsletter item')
        verbose_name_plural = _(u'newsletter items')
        ordering = ['ordering']

    def __unicode__(self):
        return u'{0}: {1}'.format(self.content_type, self.content_object)

#delete item when content object is deleted
def on_delete_newsletterable_item(sender, instance, **kwargs):
    if hasattr(instance, 'id'):
        try:
            ct = ContentType.objects.get_for_model(instance)
            item = NewsletterItem.objects.get(content_type=ct, object_id=instance.id)
            item.delete()
        except (NewsletterItem.DoesNotExist, ContentType.DoesNotExist):
            pass
pre_delete.connect(on_delete_newsletterable_item)

def create_newsletter_item(instance):
    ct = ContentType.objects.get_for_model(instance)
    if getattr(instance, 'in_newsletter', True):
        #Create a newsletter item automatically
        #An optional 'in_newsletter' field can skip the automatic creation if set to False
        return NewsletterItem.objects.get_or_create(content_type=ct, object_id=instance.id)
    elif hasattr(instance, 'in_newsletter'):
        #If 'in_newsletter' field existe and is False
        #We delete the Item if exists
        try:
            item = NewsletterItem.objects.get(content_type=ct, object_id=instance.id)
            item.delete()
            return None, True
        except NewsletterItem.DoesNotExist:
            return None, False

#create automatically a newsletter item for every objects configured as newsletter_item
def on_create_newsletterable_instance(sender, instance, created, raw, **kwargs):
    if sender in get_newsletter_item_classes():
        create_newsletter_item(instance)
post_save.connect(on_create_newsletterable_instance)

class Newsletter(models.Model):
    subject = models.CharField(max_length=200, verbose_name=_(u'subject'), blank=True, default="")
    #content = HTMLField(content_cleaner, verbose_name=_(u"content"), default="<br>", blank=True)
    content = models.TextField(_(u"content"), default="<br>", blank=True)
    items = models.ManyToManyField(NewsletterItem, blank=True)
    template = models.CharField(_(u'template'), max_length=200, default='', blank=True)
    site = models.ForeignKey(Site, verbose_name=_(u'site'), default=settings.SITE_ID)
    source_url = models.URLField(verbose_name=_(u'source url'), default="", blank=True)

    def get_items(self):
        return [item.content_object for item in self.items.all()]

    def get_items_by_category(self):
        items = self.get_items()
        def sort_by_category(item):
            category = getattr(item, 'category', None)
            if category:
                return category.ordering
            return 0
        items.sort(key=sort_by_category)
        return items


    def can_edit_newsletter(self, user):
        return user.has_perm('coop_cms.change_newsletter')
        
    def get_site_prefix(self):
        return "http://{0}".format(self.site.domain)

    def get_absolute_url(self):
        return reverse('coop_cms_view_newsletter', args=[self.id])

    def get_edit_url(self):
        return reverse('coop_cms_edit_newsletter', args=[self.id])

    def get_template_name(self):
        template = self.template
        if not template:
            self = 'coop_cms/newsletter.html'
        return template

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = _(u'newsletter')
        verbose_name_plural = _(u'newsletters')

class NewsletterSending(models.Model):

    newsletter = models.ForeignKey(Newsletter)

    scheduling_dt = models.DateTimeField(_(u"scheduling date"), blank=True, default=None, null=True)
    sending_dt = models.DateTimeField(_(u"sending date"), blank=True, default=None, null=True)

    def __unicode__(self):
        return self.newsletter.subject

    class Meta:
        verbose_name = _(u'newsletter sending')
        verbose_name_plural = _(u'newsletter sendings')

class Alias(models.Model):
    
    path = models.CharField(max_length=200)
    redirect_url = models.CharField(max_length=200, default="", blank=True)
    
    class Meta:
        verbose_name = _(u'Alias')
        verbose_name_plural = _(u'Aliases')
    
    def get_absolute_url(self):
        return reverse('coop_cms_view_article', args=[self.path])
    
    def __unicode__(self):
        return self.path
    
class FragmentType(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name=_(u"name"))
    allowed_css_classes = models.CharField(max_length=200, verbose_name=_(u"allowed css classes"), default="",
        help_text=_(u"the css classed proposed when editing a fragment. It must be separated by comas"))
    
    class Meta:
        verbose_name = _(u'Fragment type')
        verbose_name_plural = _(u'Fragment types')
        
    def __unicode__(self):
        return self.name

class FragmentFilter(models.Model):
    extra_id = models.CharField(max_length=100, db_index=True, verbose_name=_(u"extra_id"))
    
    class Meta:
        verbose_name = _(u'Fragment filter')
        verbose_name_plural = _(u'Fragment filters')
        
    def __unicode__(self):
        return self.extra_id
    
class Fragment(models.Model):
    type = models.ForeignKey(FragmentType, verbose_name=_(u'fragment type'))
    name = models.CharField(max_length=100, db_index=True, verbose_name=_(u'name'))
    css_class = models.CharField(max_length=100, default=u"", blank=True, verbose_name=_(u'CSS class'))
    position = models.IntegerField(verbose_name=_("position"), default=0)
    content = models.TextField(default=u"", blank=True, verbose_name=_(u'content'))
    filter = models.ForeignKey(FragmentFilter, verbose_name=_(u'fragment filter'), blank=True, null=True, default=None)
    
    class Meta:
        verbose_name = _(u'Fragment')
        verbose_name_plural = _(u'Fragment')
        ordering = ("position", "id")
        
    def _can_change(self, user):
        ct = ContentType.objects.get_for_model(get_article_class())
        perm = '{0}.change_{1}'.format(ct.app_label, ct.model)
        return user.has_perm(perm)

    def can_add_fragment(self, user):
        ct = ContentType.objects.get_for_model(Fragment)
        perm = '{0}.add_{1}'.format(ct.app_label, ct.model)
        return user.has_perm(perm)

    def can_edit_fragment(self, user):
        ct = ContentType.objects.get_for_model(Fragment)
        perm = '{0}.change_{1}'.format(ct.app_label, ct.model)
        return user.has_perm(perm)
        
    def save(self, *args, **kwargs):
        if not self.id and not self.position:
            max_position = Fragment.objects.filter(type=self.type, filter=self.filter).aggregate(Max('position'))['position__max'] or 0
            self.position = max_position + 1
            
        return super(Fragment, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return u"{0} {1} {2}".format(self.type, self.position, self.name)    