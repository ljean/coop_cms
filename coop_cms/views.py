# -*- coding: utf-8 -*-

from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context, Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.core.urlresolvers import reverse
import sys, json, os.path
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.template.loader import select_template
from django.db.models.aggregates import Max
from coop_cms import forms
from django.contrib.messages.api import success as success_message
from django.contrib.messages.api import error as error_message
from coop_cms import models
from django.contrib.auth.decorators import login_required
from coop_cms.settings import get_article_class, get_article_form, get_newsletter_form, get_navtree_class
from coop_cms.settings import get_new_article_form, get_article_settings_form
from djaloha import utils as djaloha_utils
from django.core.servers.basehttp import FileWrapper
import mimetypes, unicodedata
from django.conf import settings
from django.contrib import messages
from colorbox.decorators import popup_redirect, popup_close
from coop_cms.utils import send_newsletter
from coop_cms.shortcuts import get_article_or_404, get_headlines, redirect_if_alias
from django.utils.log import getLogger
from datetime import datetime
from django.utils.translation import check_for_language, activate, get_language
from urlparse import urlparse
from django.contrib.sites.models import Site
from generic_views import EditableObjectView
from django.forms.models import modelformset_factory
import logging
logger = logging.getLogger("coop_cms")

def get_article_template(article):
    template = article.template
    if not template:
        template = 'coop_cms/article.html'
    return template


def tree_map(request):
    return render_to_response(
        'coop_cms/tree_map.html',
        #{'tree': models.get_navTree_class().objects.get(id=tree_id)},  # what is the default tree for the site
        RequestContext(request)
    )

def homepage(request):
    try:
        article = get_article_class().objects.get(homepage_for_site__id=settings.SITE_ID, sites=settings.SITE_ID)
        return HttpResponseRedirect(article.get_absolute_url())
    except get_article_class().DoesNotExist:
        return HttpResponseRedirect(reverse('coop_cms_view_all_articles'))

@login_required
def view_all_articles(request):

    articles_admin_url = newsletters_admin_url = add_article_url = add_newsletter_url = None

    if request.user.is_staff:
        article_class = get_article_class()
        view_name = 'admin:%s_%s_changelist' % (article_class._meta.app_label,  article_class._meta.module_name)
        articles_admin_url = reverse(view_name)

        newsletters_admin_url = reverse('admin:coop_cms_newsletter_changelist')

        add_newsletter_url = reverse('admin:coop_cms_newsletter_add')

    Article = get_article_class()
    ct = ContentType.objects.get_for_model(Article)
    perm = '{0}.add_{1}'.format(ct.app_label, ct.model)
    if request.user.has_perm(perm):
        add_article_url = reverse('coop_cms_new_article')

    return render_to_response(
        'coop_cms/view_all_articles.html',
        {
            'articles': get_article_class().objects.filter(sites__id=settings.SITE_ID).order_by('-id')[:10],
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
        article = get_article_or_404(slug=url, sites=settings.SITE_ID) #Draft & Published
    except Http404:
        return redirect_if_alias(path=url)
    
    if not request.user.has_perm('can_view_article', article):
        raise PermissionDenied()

    editable = request.user.has_perm('can_edit_article', article)
    
    context_dict = {
        'editable': editable, 'edit_mode': False, 'article': article,
        'draft': article.publication==models.BaseArticle.DRAFT, 'headlines': get_headlines(article),
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
                [f.save() for f in djaloha_forms]

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
        'draft': article.publication==models.BaseArticle.DRAFT, 'headlines': get_headlines(article), 
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
    try:
        is_ajax = request.GET.get('page', 0)
    
        if request.session.get("coop_cms_media_doc", False):
            media_type = 'document' #force the doc
            del request.session["coop_cms_media_doc"]
    
        if media_type == 'image':
            context = {
                'images': models.Image.objects.all().order_by("-created"),
                'media_url': reverse('coop_cms_media_images'),
                'media_slide_template': 'coop_cms/slide_images_content.html',
            }
        else:
            context = {
                'documents': models.Document.objects.all().order_by("-created"),
                'media_url': reverse('coop_cms_media_documents'),
                'media_slide_template': 'coop_cms/slide_docs_content.html',
            }
        context['is_ajax'] = is_ajax
        context['media_type'] = media_type
    
        t = get_template('coop_cms/slide_base.html')
        html = t.render(RequestContext(request, context))
    
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
    try:
        if request.method == "POST":
            form = forms.AddImageForm(request.POST, request.FILES)
            if form.is_valid():
                src = form.cleaned_data['image']
                descr = form.cleaned_data['descr']
                if not descr:
                    descr = os.path.splitext(src.name)[0]
                image = models.Image(name=descr)
                image.file.save(src.name, src)
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
    try:
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
    article = get_object_or_404(get_article_class(), id=article_id)
    ArticleSettingsForm = get_article_settings_form()
    
    if not request.user.has_perm('can_edit_article', article):
        raise PermissionDenied
    
    if request.method == "POST":
        form = ArticleSettingsForm(request.user, request.POST, request.FILES, instance=article)
        if form.is_valid():
            #article.template = form.cleaned_data['template']
            article = form.save()
            return HttpResponseRedirect(article.get_absolute_url())
    else:
        form = ArticleSettingsForm(request.user, instance=article)

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
    Article = get_article_class()
    NewArticleForm = get_new_article_form()
    
    ct = ContentType.objects.get_for_model(Article)
    perm = '{0}.add_{1}'.format(ct.app_label, ct.model)

    if not request.user.has_perm(perm):
        raise PermissionDenied

    if request.method == "POST":
        form = NewArticleForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            #article.template = form.cleaned_data['template']
            article = form.save()
            success_message(request, _(u'The article has been created properly'))
            return HttpResponseRedirect(article.get_edit_url())
    else:
        form = NewArticleForm(request.user)

    return render_to_response(
        'coop_cms/popup_new_article.html',
        locals(),
        context_instance=RequestContext(request)
    )

@login_required
@popup_redirect
def new_link(request):
    ct = ContentType.objects.get_for_model(models.Link)
    perm = '{0}.add_{1}'.format(ct.app_label, ct.model)

    if not request.user.has_perm(perm):
        raise PermissionDenied

    if request.method == "POST":
        form = forms.NewLinkForm(request.POST)
        if form.is_valid():
            link = form.save()
            
            homepage_url = reverse('coop_cms_homepage')
            next = request.META.get('HTTP_REFERER', homepage_url)
            success_message(request, _(u'The link has been created properly'))
            return HttpResponseRedirect(next)
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

    #ct = ContentType.objects.get_for_model(Article)
    #perm = '{0}.add_{1}'.format(ct.app_label, ct.model)

    #if not request.user.has_perm(perm):
    #    raise PermissionDenied
    if newsletter_id:
        newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)
    else:
        newsletter = None
        
    if request.method == "POST":
        form = forms.NewNewsletterForm(request.user, request.POST, instance=newsletter)
        if form.is_valid():
            #article.template = form.cleaned_data['template']
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
                t = get_template('coop_cms/popup_update_logo.html')
                html = t.render(Context(locals()))
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
    doc = get_object_or_404(models.Document, id=doc_id)
    if not request.user.has_perm('can_download_file', doc):
        raise PermissionDenied
    
    if 'filetransfers' in settings.INSTALLED_APPS:
        from filetransfers.api import serve_file
        return serve_file(request, doc.file)
    else:
        #legacy version just kept for compatibility if filetransfers is not installed
        logger.warning("install django-filetransfers for better download support")
        file = doc.file
        file.open('rb')
        wrapper = FileWrapper(file)
        mime_type = mimetypes.guess_type(file.name)[0]
        if not mime_type:
            mime_type = u'application/octet-stream'
        response = HttpResponse(wrapper, content_type=mime_type)
        response['Content-Length'] = file.size
        filename = unicodedata.normalize('NFKD', os.path.split(file.name)[1]).encode("utf8", 'ignore')
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
            tplt = select_template(["coop_cms/navtree_content/{0}.html".format(node.content_type.name),
                                    "coop_cms/navtree_content/default.html"])
        else:
            admin_url = u""
            tplt = select_template(["coop_cms/navtree_content/default.html"])
            
        html = tplt.render(
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

        #restore exsiblings
        for n in ex_siblings.filter(ordering__gt=node.ordering):
            n.ordering -= 1
            n.save()

        #move siblings if inserted
        if ref_node:
            if ref_pos == "before":
                to_be_moved = sibling_nodes.filter(ordering__gte=ref_node.ordering)
                node.ordering = ref_node.ordering
            elif ref_pos == "after":
                to_be_moved = sibling_nodes.filter(ordering__gt=ref_node.ordering)
                node.ordering = ref_node.ordering + 1
            for n in to_be_moved:
                n.ordering += 1
                n.save()

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
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
        model_class = ct.model_class()
        object_id = request.POST['object_id']
        model_name = model_class._meta.verbose_name
        if not object_id:
            raise ValidationError(_(u"Please choose an existing {0}").format(model_name.lower()))
        try:
            object = model_class.objects.get(id=object_id)
        except model_class.DoesNotExist:
            raise ValidationError(_(u"{0} {1} not found").format(model_class._meta.verbose_name, object_id))
    
        #objects can not be added twice in the navigation tree
        if models.NavNode.objects.filter(tree=tree, content_type=ct, object_id=object.id).count() > 0:
            raise ValidationError(_(u"The {0} is already in navigation").format(model_class._meta.verbose_name))

    else:
        ct = None
        object = None

    #Create the node
    parent_id = request.POST.get('parent_id', 0)
    if parent_id:
        parent = models.NavNode.objects.get(tree=tree, id=parent_id)
    else:
        parent = None
    node = models.create_navigation_node(ct, object, tree, parent)

    response['label'] = node.label
    response['id'] = 'node_{0}'.format(node.id)
    response['message'] = _(u"'{0}' has added to the navigation tree.").format(node.label)

    return response


def get_suggest_list(request, tree):
    response = {}
    suggestions = []
    term = request.POST["term"]  # the 1st chars entered in the autocomplete

    if tree.types.count() == 0:
        nav_types = models.NavType.objects.all()
    else:
        nav_types = tree.types.all()

    for nt in nav_types:
        ct = nt.content_type
        if nt.label_rule == models.NavType.LABEL_USE_SEARCH_FIELD:
            #Get the name of the default field for the current type (eg: Page->title, Url->url ...)
            lookup = {nt.search_field + '__icontains': term}
            objects = ct.model_class().objects.filter(**lookup)
        elif nt.label_rule == models.NavType.LABEL_USE_GET_LABEL:
            objects = [obj for obj in ct.model_class().objects.all() if term.lower() in obj.get_label().lower()]
        else:
            objects = [obj for obj in ct.model_class().objects.all() if term.lower() in unicode(obj).lower()]

        already_in_navigation = [node.object_id for node in models.NavNode.objects.filter(tree=tree, content_type=ct)]
        #Get suggestions as a list of {label: object.get_label() or unicode if no get_label, 'value':<object.id>}
        for object in objects:
            if object.id not in already_in_navigation:
                #Suggest only articles which are not in navigation yet
                suggestions.append({
                    'label': models.get_object_label(ct, object),
                    'value': object.id,
                    'category': ct.model_class()._meta.verbose_name.capitalize(),
                    'type': ct.app_label + u'.' + ct.model,
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

            supported_msg = {}
            #create a map between message name and handler
            #use the function name as message id
            for fct in (view_navnode, rename_navnode, remove_navnode, move_navnode,
                add_navnode, get_suggest_list, navnode_in_navigation):
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
            response = {'status': 'error', 'message': u"An error occured : %s" % msg }
        # except:
        #     response = {'status': 'error', 'message': u"An error occured"}

        #return the result as json object
        return HttpResponse(json.dumps(response), content_type='application/json')
    raise Http404


@login_required
def edit_newsletter(request, newsletter_id):
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
                [f.save() for f in djaloha_forms]

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
    newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)

    if not request.user.has_perm('can_edit_newsletter', newsletter):
        raise PermissionDenied

    dests = settings.COOP_CMS_TEST_EMAILS

    if request.method == "POST":
        try:
            nb_sent = send_newsletter(newsletter, dests)

            messages.add_message(request, messages.SUCCESS,
                _(u"The test email has been sent to {0} addresses: {1}").format(nb_sent, u', '.join(dests)))
            return HttpResponseRedirect(newsletter.get_absolute_url())

        except Exception, msg:
            messages.add_message(request, messages.ERROR, _(u"An error occured! Please contact your support."))
            logger.error('Internal Server Error: %s' % request.path,
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
    
    ct = ContentType.objects.get_for_model(models.Fragment)
    perm = '{0}.add_{1}'.format(ct.app_label, ct.model)
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
    
    ct = ContentType.objects.get_for_model(models.Fragment)
    perm = '{0}.add_{1}'.format(ct.app_label, ct.model)
    if not request.user.has_perm(perm):
        raise PermissionDenied
    
    EditFragmentFormset = modelformset_factory(models.Fragment, forms.EditFragmentForm, extra=0)

    if request.method == "POST":
        formset = EditFragmentFormset(request.POST, queryset=models.Fragment.objects.all())
        if formset.is_valid():
            formset.save()
            return None #popup_close decorator will close and refresh
    else:
        formset = EditFragmentFormset(queryset=models.Fragment.objects.all())
    
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
    category = get_object_or_404(models.ArticleCategory, slug=slug)
    
    if not request.user.has_perm('can_view_category', category):
        raise PermissionDenied()
    
    articles = get_article_class().objects.filter(
        category=category, publication=models.BaseArticle.PUBLISHED).order_by("-publication_date")
    
    if articles.count()==0:
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

def change_language(request):
    
    try:
        from localeurl import utils as localeurl_utils
    except ImportError:
        raise Http404
    
    next = request.REQUEST.get('next', None)
    if not next:
        try:
            url = urlparse(request.META.get('HTTP_REFERER'))
            if url:
                next = url.path
        except:
            pass
    if not next:
        next = '/'
    
    if request.method == 'POST':
        
        lang_code = request.POST.get('language', None)
        if lang_code and check_for_language(lang_code):
            
            #locale is the current language
            #path is the locale-independant url
            locale, path = localeurl_utils.strip_path(next)
            
            Article = get_article_class()
            try:
                #get the translated slug of the current article
                #If switching from French to English and path is /fr/accueil/
                #The next should be : /en/home/
                
                #Get the article
                next_article = Article.objects.get(slug=path.strip('/'))
                
            except Article.DoesNotExist:
                next_article = None
                
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
            activate(lang_code)
                
            if next_article:
                next = next_article.get_absolute_url()
            else:
                next = localeurl_utils.locale_path(path, lang_code)

    return HttpResponseRedirect(next)
    
class ArticleView(EditableObjectView):
    model = get_article_class()
    form_class = get_article_form()
    field_lookup = "slug"
    varname = "article"
    
    def get_object(self):
        return get_article_or_404(slug=self.kwargs['slug'], sites=settings.SITE_ID) 
    
    def handle_object_not_found(self):
        return redirect_if_alias(path=self.kwargs['slug'])
    
    def get_headlines(self):
        return get_headlines(self.object)
    
    def get_context_data(self):
        context_data = super(ArticleView, self).get_context_data()
        context_data.update({
            'draft': self.object.publication==models.BaseArticle.DRAFT,
            'headlines': self.get_headlines(), 
            'ARTICLE_PUBLISHED': models.BaseArticle.PUBLISHED
        })
        return context_data
    
    def after_save(self, article):
        if article.temp_logo:
            article.logo = article.temp_logo
            article.temp_logo = ''
            article.save()
    
    
    def get_template(self):
        return get_article_template(self.object)
    
class EditArticleView(ArticleView):
    edit_mode = True