# -*- coding: utf-8 -*-
"""newsleters"""

from datetime import datetime
import sys

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from colorbox.decorators import popup_redirect

from coop_cms import forms
from coop_cms import models
from coop_cms.generic_views import EditableObjectView
from coop_cms.logger import logger
from coop_cms.settings import get_newsletter_form, get_newsletter_settings_form
from coop_cms.utils import send_newsletter


@login_required
@popup_redirect
def newsletter_settings(request, newsletter_id=None):
    """edit or created newsletter"""

    if newsletter_id:
        newsletter = get_object_or_404(models.Newsletter, id=newsletter_id)
    else:
        newsletter = None

    form_class = get_newsletter_settings_form()

    if request.method == "POST":
        form = form_class(request.user, request.POST, instance=newsletter)
        if form.is_valid():
            newsletter = form.save()
            return HttpResponseRedirect(newsletter.get_absolute_url())
    else:
        form = form_class(request.user, instance=newsletter)

    return render_to_response(
        'coop_cms/popup_newsletter_settings.html',
        locals(),
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


class NewsletterView(EditableObjectView):
    """newsletter view for edition"""
    model = models.Newsletter
    form_class = get_newsletter_form()
    field_lookup = "id"
    varname = "newsletter"

    def can_view_object(self):
        if self.object.is_public:
            return True
        return super(NewsletterView, self).can_edit_object()

    def get_context_data(self):
        """context"""
        context_data = super(NewsletterView, self).get_context_data()
        context_data.update({
            'title': self.object.subject,
            'by_email': self.request.GET.get('by_email', False)
        })
        return context_data

    def after_save(self, article):
        """after save"""
        pass

    def get_template(self):
        """get template"""
        return self.object.get_template_name()

