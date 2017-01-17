# -*- coding: utf-8 -*-
"""homepage management"""

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from colorbox.decorators import popup_redirect

from coop_cms import models
from coop_cms.settings import cms_no_homepage, get_article_class
from coop_cms.utils import get_homepage_url


def homepage(request):
    """view homepage"""
    if cms_no_homepage():
        raise Http404

    homepage_url = get_homepage_url()
    if homepage_url:
        return HttpResponseRedirect(homepage_url)

    return HttpResponseRedirect(reverse('coop_cms_view_all_articles'))


@login_required
@popup_redirect
def set_homepage(request, article_id):
    """use the article as homepage"""
    article = get_object_or_404(get_article_class(), id=article_id)

    if not request.user.has_perm('can_edit_article', article):
        raise PermissionDenied

    if request.method == "POST":
        site_settings = models.SiteSettings.objects.get_or_create(site=Site.objects.get_current())[0]
        site_settings.homepage_url = article.get_absolute_url()
        site_settings.save()

        return HttpResponseRedirect(reverse('coop_cms_homepage'))

    context_dict = {
        'article': article,
        'title': _(u"Do you want to use this article as homepage?"),
    }

    return render(
        request,
        'coop_cms/popup_set_homepage.html',
        context_dict
    )
