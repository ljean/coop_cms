# -*- coding: utf-8 -*-
"""views"""

from datetime import datetime
import itertools
import json
import logging
import mimetypes
import os.path
import sys
import unicodedata
from urlparse import urlparse

from django.db.models import Q
from django.db.models.aggregates import Max
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.messages.api import success as success_message, error as error_message
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.middleware.csrf import REASON_NO_REFERER, REASON_NO_CSRF_COOKIE
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context, TemplateDoesNotExist
from django.template.loader import get_template, select_template
from django.utils.translation import ugettext as _, check_for_language, activate
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from djaloha import utils as djaloha_utils
from colorbox.decorators import popup_redirect, popup_close

from coop_cms import forms
from coop_cms import models
from coop_cms.generic_views import EditableObjectView
from coop_cms.settings import (
    cms_no_homepage, get_article_class, get_article_form, get_article_settings_form,
    get_navtree_class, get_new_article_form, get_newsletter_form
)
from coop_cms.shortcuts import get_article_or_404, get_headlines, redirect_if_alias
from coop_cms.utils import send_newsletter

logger = logging.getLogger("coop_cms")


def get_article_template(article):
    """get article template"""
    template = article.template
    if not template:
        template = 'coop_cms/article.html'
    return template


def tree_map(request):
    """tree map"""
    return render_to_response(
        'coop_cms/tree_map.html',
        #{'tree': models.get_navTree_class().objects.get(id=tree_id)},  # what is the default tree for the site
        RequestContext(request)
    )


def homepage(request):
    """view homepage"""
    try:
        if cms_no_homepage():
            raise Http404
        
        site = Site.objects.get_current()
        
        #Try site settings
        try:
            site_settings = models.SiteSettings.objects.get(site=site)
            if site_settings.homepage_url:
                return HttpResponseRedirect(site_settings.homepage_url)
        except models.SiteSettings.DoesNotExist:
            pass
        
        #Try: homepage article #Deprecated
        article = get_article_class().objects.get(homepage_for_site=site, sites=site.id)
        return HttpResponseRedirect(article.get_absolute_url())
    except get_article_class().DoesNotExist:
        return HttpResponseRedirect(reverse('coop_cms_view_all_articles'))


@login_required
def view_all_articles(request):
    """all article"""

    articles_admin_url = newsletters_admin_url = add_article_url = add_newsletter_url = None

    if request.user.is_staff:
        article_class = get_article_class()
        view_name = 'admin:{0}_{1}_changelist'.format(article_class._meta.app_label, article_class._meta.module_name)
        articles_admin_url = reverse(view_name)

        newsletters_admin_url = reverse('admin:coop_cms_newsletter_changelist')

        add_newsletter_url = reverse('admin:coop_cms_newsletter_add')

    article_class = get_article_class()
    content_type = ContentType.objects.get_for_model(article_class)
    perm = '{0}.add_{1}'.format(content_type.app_label, content_type.model)
    if request.user.has_perm(perm):
        add_article_url = reverse('coop_cms_new_article')

    return render_to_response(
        'coop_cms/view_all_articles.html',
        {
            'articles': article_class.objects.filter(sites__id=settings.SITE_ID).order_by('-id')[:10],
            'newsletters': models.Newsletter.objects.all().order_by('-id')[:10],
            'editable': True,
            'articles_list_url': articles_admin_url,
            'newsletters_list_url': newsletters_admin_url,
            'add_article_url': add_article_url,
            'add_newsletter_url': add_newsletter_url,
        },
        RequestContext(request)
    )


@login_required
@popup_redirect
def set_homepage(request, article_id):
    """use the article as homepage"""
    article = get_object_or_404(get_article_class(), id=article_id)

    if not request.user.has_perm('can_edit_article', article):
        raise PermissionDenied

    if request.method == "POST":
        article.homepage_for_site = Site.objects.get(id=settings.SITE_ID)
        article.save()
        return HttpResponseRedirect(reverse('coop_cms_homepage'))

    context_dict = {
        'article': article,
        'title': _(u"Do you want to use this article as homepage?"),
    }

    return render_to_response(
        'coop_cms/popup_set_homepage.html',
        context_dict,
        context_instance=RequestContext(request)
    )


def view_article(request, url, extra_context=None, force_template=None):
    """view the article"""
    try:
        not_archived = Q(publication=models.BaseArticle.ARCHIVED)
        article = get_article_or_404(Q(slug=url) & Q(sites=settings.SITE_ID) & ~not_archived) #Draft & Published
    except Http404:
        return redirect_if_alias(path=url)
    
    if not request.user.has_perm('can_view_article', article):
        raise PermissionDenied()

    editable = request.user.has_perm('can_edit_article', article)
    
    context_dict = {
        'editable': editable, 'edit_mode': False, 'article': article,
        'draft': article.publication == models.BaseArticle.DRAFT,
        'headlines': get_headlines(article, editable=editable),
    }
    
    if extra_context:
        context_dict.update(extra_context)

    return render_to_response(
        force_template or get_article_template(article),
        context_dict,
        context_instance=RequestContext(request)
    )


@login_required
def edit_article(request, url, extra_context=None, force_template=None):
    """edit the article"""
    
    article_form_class = get_article_form()

    article = get_article_or_404(slug=url, sites=settings.SITE_ID)
    
    if not request.user.has_perm('can_edit_article', article):
        logger.error("PermissionDenied")
        error_message(request, _(u'Permission denied'))
        raise PermissionDenied

    if request.method == "POST":
        form = article_form_class(request.POST, request.FILES, instance=article)

        forms_args = djaloha_utils.extract_forms_args(request.POST)
        djaloha_forms = djaloha_utils.make_forms(forms_args, request.POST)

        if form.is_valid() and all([f.is_valid() for f in djaloha_forms]):
            article = form.save()
            
            if article.temp_logo:
                article.logo = article.temp_logo
                article.temp_logo = ''
                article.save()

            if djaloha_forms:
                for dj_form in djaloha_forms:
                    dj_form.save()

            success_message(request, _(u'The article has been saved properly'))

            return HttpResponseRedirect(article.get_absolute_url())
        else:
            error_text = u'<br />'.join([unicode(f.errors) for f in [form]+djaloha_forms if f.errors])
            error_message(request, _(u'An error occured: {0}'.format(error_text)))
            logger.debug("error: error_text")
    else:
        form = article_form_class(instance=article)

    context_dict = {
        'form': form,
        'editable': True, 'edit_mode': True, 'title': article.title,
        'draft': article.publication == models.BaseArticle.DRAFT, 'headlines': get_headlines(article),
        'article': article, 'ARTICLE_PUBLISHED': models.BaseArticle.PUBLISHED
    }
    
    if extra_context:
        context_dict.update(extra_context)

    return render_to_response(
        force_template or get_article_template(article),
        context_dict,
        context_instance=RequestContext(request)
    )


@login_required
def cancel_edit_article(request, url):
    """if cancel_edit, delete the preview image"""
    article = get_article_or_404(slug=url, sites=settings.SITE_ID)
    if article.temp_logo:
        article.temp_logo = ''
        article.save()
    return HttpResponseRedirect(article.get_absolute_url())


@login_required
@popup_redirect
def publish_article(request, url):
    """change the publication status of an article"""
    article = get_article_or_404(slug=url, sites=settings.SITE_ID)

    if not request.user.has_perm('can_publish_article', article):
        raise PermissionDenied

    draft = (article.publication == models.BaseArticle.DRAFT)
    if draft:
        article.publication = models.BaseArticle.PUBLISHED
    else:
        article.publication = models.BaseArticle.DRAFT

    if request.method == "POST":
        form = forms.PublishArticleForm(request.POST, instance=article)
        if form.is_valid():
            article = form.save()
            return HttpResponseRedirect(article.get_absolute_url())
    else:
        form = forms.PublishArticleForm(instance=article)

    context_dict = {
        'form': form,
        'article': article,
        'draft': draft,
        'title': _(u"Do you want to publish this article?") if draft else _(u"Make it draft?"),
    }

    return render_to_response(
        'coop_cms/popup_publish_article.html',
        context_dict,
        context_instance=RequestContext(request)
    )


@login_required
def show_media(request, media_type):
    """show media library"""
    try:
        if not request.user.is_staff:
            raise PermissionDenied
        
        is_ajax = request.GET.get('page', 0)
        media_filter = request.GET.get('media_filter', 0)
    
        if request.session.get("coop_cms_media_doc", False):
            media_type = 'document' #force the doc
            del request.session["coop_cms_media_doc"]
    
        if media_type == 'image':
            queryset = models.Image.objects.all().order_by("ordering", "-created")
            context = {
                'media_url': reverse('coop_cms_media_images'),
                'media_slide_template': 'coop_cms/slide_images_content.html',
            }
        else:
            media_type = "document"
            queryset = models.Document.objects.all().order_by("ordering", "-created")
            context = {
                'media_url': reverse('coop_cms_media_documents'),
                'media_slide_template': 'coop_cms/slide_docs_content.html',
            }
            
        context['is_ajax'] = is_ajax
        context['media_type'] = media_type
        
        media_filters = [media.filters.all() for media in queryset.all()] # list of lists of media_filters
        media_filters = itertools.chain(*media_filters) #flat list of media_filters
        context['media_filters'] = sorted(
            list(set(media_filters)), key=lambda mf: mf.name.upper()
        )#flat list of unique media filters sorted by alphabetical order (ignore case)
        
        if int(media_filter):
            queryset = queryset.filter(filters__id=media_filter)
            context['media_filter'] = int(media_filter)
        context[media_type+'s'] = queryset
        
        template = get_template('coop_cms/slide_base.html')
        html = template.render(RequestContext(request, context))
    
        if is_ajax:
            data = {
                'html': html,
                'media_type': media_type,
            }
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            return HttpResponse(html)
    except Exception:
        logger.exception("show_media")
        raise


@login_required
def upload_image(request):
    """upload image"""

    try:
        if not request.user.has_perm("coop_cms.add_image"):
            raise PermissionDenied()
        
        if request.method == "POST":
            form = forms.AddImageForm(request.POST, request.FILES)
            if form.is_valid():
                src = form.cleaned_data['image']
                descr = form.cleaned_data['descr']
                if not descr:
                    descr = os.path.splitext(src.name)[0]
                image = models.Image(name=descr)
                image.size = form.cleaned_data["size"]
                image.file.save(src.name, src)
                image.save()
                
                filters = form.cleaned_data['filters']
                if filters:
                    image.filters.add(*filters)
                    image.save()
                
                return HttpResponse("close_popup_and_media_slide")
        else:
            form = forms.AddImageForm()
    
        return render_to_response(
            'coop_cms/popup_upload_image.html',
            locals(),
            context_instance=RequestContext(request)
        )
    except Exception:
        logger.exception("upload_image")
        raise
        

@login_required
def upload_doc(request):
    """upload document"""
    try:
        if not request.user.has_perm("coop_cms.add_document"):
            raise PermissionDenied()
        
        if request.method == "POST":
            form = forms.AddDocForm(request.POST, request.FILES)
            if form.is_valid():
                doc = form.save()
                if not doc.name:
                    doc.name = os.path.splitext(os.path.basename(doc.file.name))[0]
                    doc.save()
    
                request.session["coop_cms_media_doc"] = True
    
                return HttpResponse("close_popup_and_media_slide")
        else:
            form = forms.AddDocForm()
    
        return render_to_response(
            'coop_cms/popup_upload_doc.html',
            locals(),
            context_instance=RequestContext(request)
        )
    except Exception:
        logger.exception("upload_doc")
        raise


@login_required
@popup_redirect
def change_template(request, article_id):
    """change template"""

    article = get_object_or_404(get_article_class(), id=article_id)
    if request.method == "POST":
        form = forms.ArticleTemplateForm(article, request.user, request.POST, request.FILES)
        if form.is_valid():
            article.template = form.cleaned_data['template']
            article.save()
            return HttpResponseRedirect(article.get_edit_url())
    else:
        form = forms.ArticleTemplateForm(article, request.user)

    return render_to_response(
        'coop_cms/popup_change_template.html',
        locals(),
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def article_settings(request, article_id):
    """article settings"""
    article = get_object_or_404(get_article_class(), id=article_id)
    article_settings_form_class = get_article_settings_form()
    
    if not request.user.has_perm('can_edit_article', article):
        raise PermissionDenied
    
    if request.method == "POST":
        form = article_settings_form_class(request.user, request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save()
            form.save_m2m()
            return HttpResponseRedirect(article.get_absolute_url())
    else:
        form = article_settings_form_class(request.user, instance=article)

    context = {
        'article': article,
        'form': form,
    }
    return render_to_response(
        'coop_cms/popup_article_settings.html',
        context,
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def new_article(request):
    """new article"""
    article_class = get_article_class()
    new_article_form = get_new_article_form()
    
    content_type = ContentType.objects.get_for_model(article_class)
    perm = '{0}.add_{1}'.format(content_type.app_label, content_type.model)

    if not request.user.has_perm(perm):
        raise PermissionDenied

    if request.method == "POST":
        form = new_article_form(request.user, request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            form.save_m2m()
            success_message(request, _(u'The article has been created properly'))
            return HttpResponseRedirect(article.get_edit_url())
    else:
        form = new_article_form(request.user)

    return render_to_response(
        'coop_cms/popup_new_article.html',
        locals(),
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def new_link(request):
    """new link"""
    content_type = ContentType.objects.get_for_model(models.Link)
    perm = '{0}.add_{1}'.format(content_type.app_label, content_type.model)

    if not request.user.has_perm(perm):
        raise PermissionDenied

    if request.method == "POST":
        form = forms.NewLinkForm(request.POST)
        if form.is_valid():
            form.save()
            homepage_url = reverse('coop_cms_homepage')
            next_url = request.META.get('HTTP_REFERER', homepage_url)
            success_message(request, _(u'The link has been created properly'))
            return HttpResponseRedirect(next_url)
    else:
        form = forms.NewLinkForm()
        
    context = {
        'form': form,
    }

    return render_to_response(
        'coop_cms/popup_new_link.html',
        context,
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def new_newsletter(request, newsletter_id=None):
    """new newsletter"""

    if newsletter_id:
        newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)
    else:
        newsletter = None
        
    if request.method == "POST":
        form = forms.NewNewsletterForm(request.user, request.POST, instance=newsletter)
        if form.is_valid():
            newsletter = form.save()
            return HttpResponseRedirect(newsletter.get_edit_url())
    else:
        form = forms.NewNewsletterForm(request.user, instance=newsletter)

    return render_to_response(
        'coop_cms/popup_new_newsletter.html',
        locals(),
        context_instance=RequestContext(request)
    )


@login_required
def update_logo(request, article_id):
    """update logo"""
    try:
        article = get_object_or_404(get_article_class(), id=article_id)
        if request.method == "POST":
            form = forms.ArticleLogoForm(request.POST, request.FILES)
            if form.is_valid():
                article.temp_logo = form.cleaned_data['image']
                article.save()
                url = article.logo_thumbnail(True).url
                data = {'ok': True, 'src': url}
                return HttpResponse(json.dumps(data), content_type='application/json')
            else:
                template = get_template('coop_cms/popup_update_logo.html')
                html = template.render(Context(locals()))
                data = {'ok': False, 'html': html}
                return HttpResponse(json.dumps(data), content_type='application/json')
        else:
            form = forms.ArticleLogoForm()
    
        return render_to_response(
            'coop_cms/popup_update_logo.html',
            locals(),
            context_instance=RequestContext(request)
        )
    except Exception:
        logger.exception("update_logo")
        raise


@login_required
def download_doc(request, doc_id):
    """download a doc"""
    doc = get_object_or_404(models.Document, id=doc_id)
    if not request.user.has_perm('can_download_file', doc):
        raise PermissionDenied
    
    if 'filetransfers' in settings.INSTALLED_APPS:
        from filetransfers.api import serve_file # pylint: disable=F0401
        return serve_file(request, doc.file)
    else:
        #legacy version just kept for compatibility if filetransfers is not installed
        logger.warning("install django-filetransfers for better download support")
        the_file = doc.file
        the_file.open('rb')
        wrapper = FileWrapper(the_file)
        mime_type = mimetypes.guess_type(the_file.name)[0]
        if not mime_type:
            mime_type = u'application/octet-stream'
        response = HttpResponse(wrapper, content_type=mime_type)
        response['Content-Length'] = the_file.size
        filename = unicodedata.normalize('NFKD', os.path.split(the_file.name)[1]).encode("utf8", 'ignore')
        filename = filename.replace(' ', '-')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        return response

#navigation tree --------------------------------------------------------------


def view_navnode(request, tree):
    """show info about the node when selected"""
    try:
        response = {}
    
        node_id = request.POST['node_id']
        node = models.NavNode.objects.get(tree=tree, id=node_id)
        model_name = object_label = ""
    
        #get the admin url
        if node.content_type:
            app, mod = node.content_type.app_label, node.content_type.model
            admin_url = reverse("admin:{0}_{1}_change".format(app, mod), args=(node.object_id,))
    
            #load and render template for the object
            #try to load the corresponding template and if not found use the default one
            model_name = unicode(node.content_type)
            object_label = unicode(node.content_object)
            template = select_template([
                "coop_cms/navtree_content/{0}.html".format(node.content_type.name),
                "coop_cms/navtree_content/default.html"
            ])
        else:
            admin_url = u""
            template = select_template(["coop_cms/navtree_content/default.html"])
            
        html = template.render(
            RequestContext(request, {
                "node": node, "admin_url": admin_url,
                "model_name": model_name, "object_label": object_label
            })
        )
    
        #return data has dictionnary
        response['html'] = html
        response['message'] = u"Node content loaded."
    
        return response
    except Exception:
        logger.exception("view_navnode")
        raise


def rename_navnode(request, tree):
    """change the name of a node when renamed in the tree"""
    response = {}
    node_id = request.POST['node_id']
    node = models.NavNode.objects.get(tree=tree, id=node_id)  # get the node
    old_name = node.label  # get the old name for success message
    node.label = request.POST['name']  # change the name
    node.save()
    if old_name != node.label:
        response['message'] = _(u"The node '{0}' has been renamed into '{1}'.").format(old_name, node.label)
    else:
        response['message'] = ''
    return response


def remove_navnode(request, tree):
    """delete a node"""
    #Keep multi node processing even if multi select is not allowed
    response = {}
    node_ids = request.POST['node_ids'].split(";")
    for node_id in node_ids:
        models.NavNode.objects.get(tree=tree, id=node_id).delete()
    if len(node_ids) == 1:
        response['message'] = _(u"The node has been removed.")
    else:
        response['message'] = _(u"{0} nodes has been removed.").format(len(node_ids))
    return response


def move_navnode(request, tree):
    """move a node in the tree"""
    response = {}

    node_id = request.POST['node_id']
    ref_pos = request.POST['ref_pos']
    parent_id = request.POST.get('parent_id', 0)
    ref_id = request.POST.get('ref_id', 0)

    node = models.NavNode.objects.get(tree=tree, id=node_id)

    if parent_id:
        sibling_nodes = models.NavNode.objects.filter(tree=tree, parent__id=parent_id)
        parent_node = models.NavNode.objects.get(tree=tree, id=parent_id)
    else:
        sibling_nodes = models.NavNode.objects.filter(tree=tree, parent__isnull=True)
        parent_node = None

    if ref_id:
        ref_node = models.NavNode.objects.get(tree=tree, id=ref_id)
    else:
        ref_node = None

    #Update parent if changed
    if parent_node != node.parent:
        if node.parent:
            ex_siblings = models.NavNode.objects.filter(tree=tree, parent=node.parent).exclude(id=node.id)
        else:
            ex_siblings = models.NavNode.objects.filter(tree=tree, parent__isnull=True).exclude(id=node.id)

        node.parent = parent_node

        #restore ex-siblings
        for sib_node in ex_siblings.filter(ordering__gt=node.ordering):
            sib_node.ordering -= 1
            sib_node.save()

        #move siblings if inserted
        if ref_node:
            if ref_pos == "before":
                to_be_moved = sibling_nodes.filter(ordering__gte=ref_node.ordering)
                node.ordering = ref_node.ordering
            elif ref_pos == "after":
                to_be_moved = sibling_nodes.filter(ordering__gt=ref_node.ordering)
                node.ordering = ref_node.ordering + 1
            for ntbm in to_be_moved:
                ntbm.ordering += 1
                ntbm.save()

        else:
            #add at the end
            max_ordering = sibling_nodes.aggregate(max_ordering=Max('ordering'))['max_ordering'] or 0
            node.ordering = max_ordering + 1

    else:

        #Update pos if changed
        if ref_node:
            if ref_node.ordering > node.ordering:
                #move forward
                to_be_moved = sibling_nodes.filter(ordering__lt=ref_node.ordering, ordering__gt=node.ordering)
                for next_sibling_node in to_be_moved:
                    next_sibling_node.ordering -= 1
                    next_sibling_node.save()

                if ref_pos == "before":
                    node.ordering = ref_node.ordering - 1
                elif ref_pos == "after":
                    node.ordering = ref_node.ordering
                    ref_node.ordering -= 1
                    ref_node.save()

            elif ref_node.ordering < node.ordering:
                #move backward
                to_be_moved = sibling_nodes.filter(ordering__gt=ref_node.ordering, ordering__lt=node.ordering)
                for next_sibling_node in to_be_moved:
                    next_sibling_node.ordering += 1
                    next_sibling_node.save()

                if ref_pos == "before":
                    node.ordering = ref_node.ordering
                    ref_node.ordering += 1
                    ref_node.save()
                elif ref_pos == "after":
                    node.ordering = ref_node.ordering + 1

        else:
            max_ordering = sibling_nodes.aggregate(max_ordering=Max('ordering'))['max_ordering'] or 0
            node.ordering = max_ordering + 1

    node.save()
    response['message'] = _(u"The node '{0}' has been moved.").format(node.label)

    return response


def add_navnode(request, tree):
    """Add a new node"""
    response = {}

    #get the type of object
    object_type = request.POST['object_type']
    if object_type:
        app_label, model_name = object_type.split('.')
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        model_class = content_type.model_class()
        object_id = request.POST['object_id']
        model_name = model_class._meta.verbose_name
        if not object_id:
            raise ValidationError(_(u"Please choose an existing {0}").format(model_name.lower()))
        try:
            obj = model_class.objects.get(id=object_id)
        except model_class.DoesNotExist:
            raise ValidationError(_(u"{0} {1} not found").format(model_class._meta.verbose_name, object_id))
    
        #objects can not be added twice in the navigation tree
        if models.NavNode.objects.filter(tree=tree, content_type=content_type, object_id=obj.id).count() > 0:
            raise ValidationError(_(u"The {0} is already in navigation").format(model_class._meta.verbose_name))

    else:
        content_type = None
        obj = None

    #Create the node
    parent_id = request.POST.get('parent_id', 0)
    if parent_id:
        parent = models.NavNode.objects.get(tree=tree, id=parent_id)
    else:
        parent = None
    node = models.create_navigation_node(content_type, obj, tree, parent)

    response['label'] = node.label
    response['id'] = 'node_{0}'.format(node.id)
    response['message'] = _(u"'{0}' has added to the navigation tree.").format(node.label)

    return response


def get_suggest_list(request, tree):
    """call by auto-complete"""
    response = {}
    suggestions = []
    term = request.POST["term"]  # the 1st chars entered in the autocomplete

    if tree.types.count() == 0:
        nav_types = models.NavType.objects.all()
    else:
        nav_types = tree.types.all()

    for nav_type in nav_types:
        content_type = nav_type.content_type
        if nav_type.label_rule == models.NavType.LABEL_USE_SEARCH_FIELD:
            #Get the name of the default field for the current type (eg: Page->title, Url->url ...)
            lookup = {nav_type.search_field + '__icontains': term}
            objects = content_type.model_class().objects.filter(**lookup)
        elif nav_type.label_rule == models.NavType.LABEL_USE_GET_LABEL:
            objects = [
                obj for obj in content_type.model_class().objects.all() if term.lower() in obj.get_label().lower()
            ]
        else:
            objects = [
                obj for obj in content_type.model_class().objects.all() if term.lower() in unicode(obj).lower()
            ]

        already_in_navigation = [
            node.object_id for node in models.NavNode.objects.filter(tree=tree, content_type=content_type)
        ]

        #Get suggestions as a list of {label: object.get_label() or unicode if no get_label, 'value':<object.id>}
        for obj in objects:
            if obj.id not in already_in_navigation:
                #Suggest only articles which are not in navigation yet
                suggestions.append({
                    'label': models.get_object_label(content_type, obj),
                    'value': obj.id,
                    'category': content_type.model_class()._meta.verbose_name.capitalize(),
                    'type': content_type.app_label + u'.' + content_type.model,
                })

    #Add suggestion for an empty node
    suggestions.append({
        'label': _(u"Node"),
        'value': 0,
        'category': _(u"Empty node"),
        'type': "",
    })
    response['suggestions'] = suggestions
    return response


def navnode_in_navigation(request, tree):
    """toogle the is_visible_flag of a navnode"""
    response = {}
    node_id = request.POST['node_id']
    node = models.NavNode.objects.get(tree=tree, id=node_id)  # get the node
    node.in_navigation = not node.in_navigation
    node.save()
    if node.in_navigation:
        response['message'] = _(u"The node is now visible.")
        response['label'] = _(u"Hide node in navigation")
        response['icon'] = "in_nav"
    else:
        response['message'] = _(u"The node is now hidden.")
        response['label'] = _(u"Show node in navigation")
        response['icon'] = "out_nav"
    return response


@login_required
def process_nav_edition(request, tree_id):
    """This handle ajax request sent by the tree component"""
    if request.method == 'POST' and request.is_ajax() and 'msg_id' in request.POST:
        try:
            #Get the current tree
            tree_class = get_navtree_class()
            tree = get_object_or_404(tree_class, id=tree_id)

            #check permissions
            perm_name = "{0}.change_{1}".format(tree_class._meta.app_label, tree_class._meta.module_name)
            if not request.user.has_perm(perm_name):
                raise PermissionDenied

            functions = (
                view_navnode, rename_navnode, remove_navnode, move_navnode,
                add_navnode, get_suggest_list, navnode_in_navigation,
            )
            supported_msg = {}
            #create a map between message name and handler
            #use the function name as message id
            for fct in functions:
                supported_msg[fct.__name__] = fct

            #Call the handler corresponding to the requested message
            response = supported_msg[request.POST['msg_id']](request, tree)

            #If no exception raise: Success
            response['status'] = 'success'
            response.setdefault('message', 'Ok')  # if no message defined in response, add something

        except KeyError, msg:
            response = {'status': 'error', 'message': u"Unsupported message : %s" % msg}
        except PermissionDenied:
            response = {'status': 'error', 'message': u"You are not allowed to add a node"}
        except ValidationError, ex:
            response = {'status': 'error', 'message': u' - '.join(ex.messages)}
        except Exception, msg:
            logger.exception("process_nav_edition")
            response = {'status': 'error', 'message': u"An error occured : %s" % msg}

        #return the result as json object
        return HttpResponse(json.dumps(response), content_type='application/json')
    raise Http404


@login_required
def edit_newsletter(request, newsletter_id):
    """edit newsletter"""
    newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)
    newsletter_form_class = get_newsletter_form()

    if not request.user.has_perm('can_edit_newsletter', newsletter):
        raise PermissionDenied

    if request.method == "POST":
        form = newsletter_form_class(request.POST, instance=newsletter)

        forms_args = djaloha_utils.extract_forms_args(request.POST)
        djaloha_forms = djaloha_utils.make_forms(forms_args, request.POST)

        if form.is_valid() and all([f.is_valid() for f in djaloha_forms]):
            newsletter = form.save()

            if djaloha_forms:
                for dj_form in djaloha_forms:
                    dj_form.save()

            success_message(request, _(u'The newsletter has been saved properly'))

            return HttpResponseRedirect(reverse('coop_cms_view_newsletter', args=[newsletter.id]))
    else:
        form = newsletter_form_class(instance=newsletter)

    context_dict = {
        'form': form, 'post_url': reverse('coop_cms_edit_newsletter', args=[newsletter.id]),
        'editable': True, 'edit_mode': True, 'title': newsletter.subject,
        'newsletter': newsletter,
    }

    return render_to_response(
        newsletter.get_template_name(),
        context_dict,
        context_instance=RequestContext(request)
    )


def view_newsletter(request, newsletter_id):
    """view newsletter"""
    newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)

    context_dict = {
        'title': newsletter.subject, 'newsletter': newsletter,
        'editable': request.user.is_authenticated(), 'by_email': False,
    }

    return render_to_response(
        newsletter.get_template_name(),
        context_dict,
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def change_newsletter_template(request, newsletter_id):
    """change newsletter template"""
    newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)

    if not request.user.has_perm('can_edit_newsletter', newsletter):
        raise PermissionDenied

    if request.method == "POST":
        form = forms.NewsletterTemplateForm(newsletter, request.user, request.POST)
        if form.is_valid():
            newsletter.template = form.cleaned_data['template']
            newsletter.save()
            return HttpResponseRedirect(newsletter.get_edit_url())
    else:
        form = forms.NewsletterTemplateForm(newsletter, request.user)

    return render_to_response(
        'coop_cms/popup_change_newsletter_template.html',
        {'form': form, 'newsletter': newsletter},
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def test_newsletter(request, newsletter_id):
    """test newsletter"""
    newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)

    if not request.user.has_perm('can_edit_newsletter', newsletter):
        raise PermissionDenied

    dests = settings.COOP_CMS_TEST_EMAILS

    if request.method == "POST":
        try:
            nb_sent = send_newsletter(newsletter, dests)

            messages.add_message(
                request, messages.SUCCESS,
                _(u"The test email has been sent to {0} addresses: {1}").format(nb_sent, u', '.join(dests))
            )
            return HttpResponseRedirect(newsletter.get_absolute_url())

        except Exception:
            messages.add_message(request, messages.ERROR, _(u"An error occured! Please contact your support."))
            logger.error(
                'Internal Server Error: {0}'.format(request.path),
                exc_info=sys.exc_info,
                extra={
                    'status_code': 500,
                    'request': request
                }
            )
            return HttpResponseRedirect(newsletter.get_absolute_url())

    return render_to_response(
        'coop_cms/popup_test_newsletter.html',
        {'newsletter': newsletter, 'dests': dests},
        context_instance=RequestContext(request)
    )


@login_required
@popup_redirect
def schedule_newsletter_sending(request, newsletter_id):
    """schedule sending"""
    newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)
    instance = models.NewsletterSending(newsletter=newsletter)

    if request.method == "POST":
        form = forms.NewsletterSchedulingForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(newsletter.get_edit_url())
    else:
        form = forms.NewsletterSchedulingForm(instance=instance, initial={'scheduling_dt': datetime.now()})

    return render_to_response(
        'coop_cms/popup_schedule_newsletter_sending.html',
        {'newsletter': newsletter, 'form': form},
        context_instance=RequestContext(request)
    )


@login_required
@popup_close
def add_fragment(request):
    """add a fragment to the current template"""
    
    content_type = ContentType.objects.get_for_model(models.Fragment)
    perm = '{0}.add_{1}'.format(content_type.app_label, content_type.model)
    if not request.user.has_perm(perm):
        raise PermissionDenied

    if request.method == "POST":
        form = forms.AddFragmentForm(request.POST)
        if form.is_valid():
            form.save()
            return None #popup_close decorator will close and refresh
    else:
        form = forms.AddFragmentForm()
        
    context_dict = {
        'form': form,
    }

    return render_to_response(
        'coop_cms/popup_add_fragment.html',
        context_dict,
        context_instance=RequestContext(request)
    )


@login_required
@popup_close
def edit_fragments(request):
    """edit fragments of the current template"""
    
    content_type = ContentType.objects.get_for_model(models.Fragment)
    perm = '{0}.add_{1}'.format(content_type.app_label, content_type.model)
    if not request.user.has_perm(perm):
        raise PermissionDenied
    
    edit_fragment_formset = modelformset_factory(models.Fragment, forms.EditFragmentForm, extra=0)

    if request.method == "POST":
        formset = edit_fragment_formset(request.POST, queryset=models.Fragment.objects.all())
        if formset.is_valid():
            formset.save()
            return None #popup_close decorator will close and refresh
    else:
        formset = edit_fragment_formset(queryset=models.Fragment.objects.all())
    
    context_dict = {
        'form': formset,
        'title': _(u"Edit fragments of this template?"),
    }

    return render_to_response(
        'coop_cms/popup_edit_fragments.html',
        context_dict,
        context_instance=RequestContext(request)
    )


def articles_category(request, slug):
    """view articles by category"""
    category = get_object_or_404(models.ArticleCategory, slug=slug, sites__id=settings.SITE_ID)
    
    if not request.user.has_perm('can_view_category', category):
        raise PermissionDenied()
    
    articles = category.get_articles_qs().filter(
        publication=models.BaseArticle.PUBLISHED
    ).order_by("-publication_date")
    
    if articles.count() == 0:
        raise Http404
    
    try:
        category_template = u"coop_cms/categories/{0}.html".format(category.slug)
        get_template(category_template)
    except TemplateDoesNotExist:
        category_template = "coop_cms/articles_category.html"
    
    return render_to_response(
        category_template,
        {'category': category, "articles": articles},
        context_instance=RequestContext(request)
    )


@csrf_exempt
def hide_accept_cookies_message(request):
    """force cookie warning message to be hidden"""
    if request.method == 'POST':
        request.session['hide_accept_cookie_message'] = True
        data = {"Ok": True}
        return HttpResponse(json.dumps(data), content_type="application/json")
    raise Http404


@csrf_exempt
def change_language(request):
    """change the language"""
    try:
        from localeurl import utils as localeurl_utils # pylint: disable=F0401
    except ImportError:
        raise Http404
    
    next_url = request.REQUEST.get('next', None)
    if not next_url:
        try:
            url = urlparse(request.META.get('HTTP_REFERER'))
            if url:
                next_url = url.path
        except Exception:
            pass
    
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        after_change_url = request.POST.get('next_url_after_change_lang', None)
        if after_change_url:
            next_url = after_change_url
            
        if lang_code and check_for_language(lang_code):
            
            #path is the locale-independant url
            path = localeurl_utils.strip_path(next_url)[1]
            
            article_class = get_article_class()
            try:
                #get the translated slug of the current article
                #If switching from French to English and path is /fr/accueil/
                #The next should be : /en/home/
                
                #Get the article
                next_article = article_class.objects.get(slug=path.strip('/'))
                
            except article_class.DoesNotExist:
                next_article = None
            
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            #else:
                #response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
            activate(lang_code)
            
            if next_article:
                next_url = next_article.get_absolute_url()
            else:
                next_url = localeurl_utils.locale_path(path, lang_code)

    if not next_url:
        next_url = '/'
    
    return HttpResponseRedirect(next_url)


class ArticleView(EditableObjectView):
    """Article view for edition"""
    model = get_article_class()
    form_class = get_article_form()
    field_lookup = "slug"
    varname = "article"
    
    def get_object(self):
        """get object"""
        return get_article_or_404(slug=self.kwargs['slug'], sites=settings.SITE_ID)
    
    def can_access_object(self):
        """perms -> 404 if no perms"""
        if self.object.is_archived():
            return super(ArticleView, self).can_view_object()
        return True
    
    def handle_object_not_found(self):
        """go to alias if not found"""
        return redirect_if_alias(path=self.kwargs['slug'])
    
    def get_headlines(self):
        """headline"""
        return get_headlines(self.object)
    
    def get_context_data(self):
        """context"""
        context_data = super(ArticleView, self).get_context_data()
        context_data.update({
            'draft': self.object.publication == models.BaseArticle.DRAFT,
            'headlines': self.get_headlines(), 
            'ARTICLE_PUBLISHED': models.BaseArticle.PUBLISHED
        })
        return context_data
    
    def after_save(self, article):
        """after save"""
        if article.temp_logo:
            article.logo = article.temp_logo
            article.temp_logo = ''
            article.save()

    def get_template(self):
        """get template"""
        return get_article_template(self.object)


class EditArticleView(ArticleView):
    """editable version"""
    edit_mode = True


class DebugErrorCodeView(TemplateView):
    """Debugging: view error page in debug"""

    def get_template_names(self):
        """template to view"""
        return ("{0}.html".format(self.kwargs["error_code"]),)


def csrf_failure(request, reason=""):
    """
    Custom view used when request fails CSRF protection.
    
    ENABLED by default by coop_cms unless you set COOP_CMS_DO_NOT_INSTALL_CSRF_FAILURE_VIEW=True in settings.py
    """
    
    logger.warn(u"csrf_failure, reason: {0}".format(reason))
    
    template = get_template('coop_cms/csrf_403.html')
    
    context = Context({
        'DEBUG': settings.DEBUG,
        'cookie_disabled': reason == REASON_NO_CSRF_COOKIE,
        'no_referer': reason == REASON_NO_REFERER,
    })

    html = template.render(RequestContext(request, context))
    
    return HttpResponseForbidden(html, content_type='text/html')
