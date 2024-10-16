# -*- coding: utf-8 -*-
"""media library"""

import itertools
import json
import os.path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse

from ..forms.content import AddDocForm, AddImageForm
from ..logger import logger
from .. import models
from ..moves import make_context
from ..utils import paginate
from ..utils.xsendfile import serve_file


def _get_photologue_media(request):
    """get photologue media"""
    # Only if django-photologue is installed
    if "photologue" in settings.INSTALLED_APPS:
        from photologue.models import Photo, Gallery
        media_url = reverse('coop_cms_media_photologue')
        gallery_filter = request.GET.get('gallery_filter', 0)
        queryset = Photo.objects.all().order_by("-date_added")
        if gallery_filter:
            queryset = queryset.filter(galleries__id=gallery_filter)
            media_url += "?gallery_filter={0}".format(gallery_filter)

        context = {
            'media_url': media_url,
            'media_slide_template': 'coop_cms/medialib/slide_photologue_content.html',
            'gallery_filter': int(gallery_filter),
            'galleries': Gallery.objects.all(),
        }
        return queryset, context
    else:
        raise Http404


@login_required(login_url=reverse_lazy('login'))
def show_media(request, media_type):
    """show media library"""
    try:
        can_view_image = request.user.has_perm("coop_cms.view_image")
        can_view_document = request.user.has_perm("coop_cms.view_document")

        if not (can_view_image or can_view_document):
            raise PermissionDenied

        try:
            page = int(request.GET.get('page', 0) or 0)
        except ValueError:
            page = 1
        is_ajax = page > 0
        media_filter = request.GET.get('media_filter', 0)
        skip_media_filter = False

        if request.session.get("coop_cms_media_doc", False):
            if not can_view_document:
                raise PermissionDenied
            # force the doc
            media_type = 'document'
            del request.session["coop_cms_media_doc"]

        if media_type == 'image':
            if not can_view_image:
                raise PermissionDenied
            queryset = models.Image.objects.all().order_by("ordering", "-created")
            context = {
                'media_url': reverse('coop_cms_media_images'),
                'media_slide_template': 'coop_cms/medialib/slide_images_content.html',
            }

        elif media_type == 'photologue':
            queryset, context = _get_photologue_media(request)
            skip_media_filter = True

        else:
            media_type = "document"
            queryset = models.Document.objects.all().order_by("ordering", "-created")
            context = {
                'media_url': reverse('coop_cms_media_documents'),
                'media_slide_template': 'coop_cms/medialib/slide_docs_content.html',
            }

        context['is_ajax'] = is_ajax
        context['media_type'] = media_type
        context['can_view_image'] = can_view_image
        context['can_view_document'] = can_view_document
        context['can_view_image'] = can_view_image

        if not skip_media_filter:
            # list of lists of media_filters
            media_filters = [media.filters.all() for media in queryset.all()]
            # flat list of media_filters
            media_filters = itertools.chain(*media_filters)
            # flat list of unique media filters sorted by alphabetical order (ignore case)
            context['media_filters'] = sorted(
                list(set(media_filters)), key=lambda mf: mf.name.upper()
            )

            if int(media_filter):
                queryset = queryset.filter(filters__id=media_filter)
                context['media_filter'] = int(media_filter)

        page_obj = paginate(request, queryset, 12)

        context[media_type+'s'] = list(page_obj)
        context['page_obj'] = page_obj

        context["allow_photologue"] = "photologue" in settings.INSTALLED_APPS

        if int(media_filter):
            context["media_url"] += '?media_filter={0}'.format(media_filter)

        template = get_template('coop_cms/medialib/slide_base.html')
        html = template.render(make_context(request, context))

        if is_ajax:
            data = {
                'html': html,
                'media_type': media_type,
                'media_url': context["media_url"],
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
            form = AddImageForm(request.POST, request.FILES)
            if form.is_valid():
                src = form.cleaned_data['image']
                description = form.cleaned_data['descr']
                copyright = form.cleaned_data['copyright']
                if not description:
                    description = os.path.splitext(src.name)[0]
                image = models.Image(name=description, copyright=copyright)
                image.size = form.cleaned_data["size"]
                image.file.save(src.name, src)
                image.alt_text = form.cleaned_data.get('alt_text', '')
                image.title = form.cleaned_data.get('title' '')
                image.save()

                filters = form.cleaned_data['filters']
                if filters:
                    image.filters.add(*filters)
                    image.save()

                return HttpResponse("close_popup_and_media_slide")
        else:
            form = AddImageForm()

        return render(
            request,
            'coop_cms/popup_upload_image.html',
            {
                'form': form,
            }
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
            form = AddDocForm(request.POST, request.FILES)
            if form.is_valid():
                doc = form.save()
                if not doc.name:
                    doc.name = os.path.splitext(os.path.basename(doc.file.name))[0]
                    doc.save()

                filters = form.cleaned_data['filters']
                if filters:
                    doc.filters.add(*filters)
                    doc.save()

                request.session["coop_cms_media_doc"] = True

                return HttpResponse("close_popup_and_media_slide")
        else:
            form = AddDocForm()

        return render(
            request,
            'coop_cms/popup_upload_doc.html',
            locals()
        )
    except Exception:
        logger.exception("upload_doc")
        raise


@login_required
def download_doc(request, doc_id):
    """download a doc"""
    doc = get_object_or_404(models.Document, id=doc_id)
    if not request.user.has_perm('can_download_file', doc):
        raise PermissionDenied
    return serve_file(request, doc.file.file, save_as=True)
