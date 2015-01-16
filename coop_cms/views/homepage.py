# -*- coding: utf-8 -*-
"""homepage management"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from colorbox.decorators import popup_redirect

from coop_cms import models
from coop_cms.settings import cms_no_homepage, get_article_class


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
