# -*- coding: utf-8 -*-
"""emailing views"""

import datetime
import os.path

from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template

from coop_cms.utils import redirect_to_language
from wsgiref.util import FileWrapper

from . import models
from . import forms
from .utils import get_emailing_context, patch_emailing_html


def view_link(request, link_uuid, contact_uuid):
    """view magic link"""
    link = get_object_or_404(models.MagicLink, uuid=link_uuid)
    try:
        user = models.Contact.objects.get(uuid=contact_uuid)
        link.visitors.add(user)
    except models.Contact.DoesNotExist:
        pass
    return HttpResponseRedirect(link.url)


def unregister_contact(request, emailing_id, contact_uuid):
    """contact unregister from emailing list"""

    contact = get_object_or_404(models.Contact, uuid=contact_uuid)
    try:
        emailing = models.Emailing.objects.get(id=emailing_id)
    except models.Emailing.DoesNotExist:
        raise Http404

    if request.method == "POST":
        if 'unregister' in request.POST:
            form = forms.UnregisterForm(request.POST)
            if form.is_valid():
                if emailing and emailing.subscription_type:
                    subscription = models.Subscription.objects.get_or_create(
                        contact=contact, subscription_type=emailing.subscription_type
                    )[0]
                    subscription.accept_subscription = False
                    subscription.unsubscription_date = datetime.datetime.now()
                    subscription.save()
                    emailing.unsub.add(contact)
                    emailing.save()
                return render(
                    request,
                    'newsletters/public/unregister_done.html',
                    {
                        'contact': contact,
                        'emailing': emailing,
                        'form': form,
                        'unregister': True,
                    }
                )
            else:
                pass  # not valid : display with errors

        else:
            return render(
                request,
                'newsletters/public/unregister_done.html',
                {
                    'contact': contact,
                    'emailing': emailing,
                }
            )
    else:
        form = forms.UnregisterForm()

    return render(
        request,
        'newsletters/public/unregister_confirm.html',
        {
            'contact': contact,
            'emailing': emailing,
            'form': form,
        }
    )


def view_emailing_online(request, emailing_id, contact_uuid):
    """view an emailing online"""
    contact = get_object_or_404(models.Contact, uuid=contact_uuid)
    emailing = get_object_or_404(models.Emailing, id=emailing_id)
    context = get_emailing_context(emailing, contact)
    the_template = get_template(emailing.newsletter.get_template_name())
    html_text = the_template.render(context)
    html_text = patch_emailing_html(html_text, emailing, contact)
    return HttpResponse(html_text)


def view_emailing_online_lang(request, emailing_id, contact_uuid, lang):
    """view an emailing in a given lang"""
    url = reverse("newsletters:view_online", args=[emailing_id, contact_uuid])
    return redirect_to_language(url, lang)


def email_tracking(request, emailing_id, contact_uuid):
    """handle download of email opening tracking image"""
    emailing = get_object_or_404(models.Emailing, id=emailing_id)
    contact = get_object_or_404(models.Contact, uuid=contact_uuid)

    emailing.opened_emails.add(contact)
    emailing.save()

    dir_name = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(dir_name, "files/email-tracking.png")
    response = HttpResponse(FileWrapper(open(file_name, 'rb')), content_type='image/png')
    response['Content-Length'] = os.path.getsize(file_name)
    return response
