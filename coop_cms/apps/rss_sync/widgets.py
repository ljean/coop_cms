# -*- coding: utf-8 -*-
"""widgets"""

from django.forms import HiddenInput
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from coop_cms.apps.rss_sync.models import RssSource


def get_button_code(label, url, is_default=False):
    """create a html button"""
    css_class = u' default' if is_default else ''
    html = "&nbsp;&nbsp;"
    html += """<button class="btn btn-primary cust-btn{2}" onclick="window.location=\'{1}\'">{0}</button>""".format(
        label, url, css_class
    )

    #javascript code for moving the button to the submit-row at the bottom of the page
    html += "<script>django.jQuery(function() {django.jQuery('.cust-btn').appendTo('.submit-row')});</script>"
    return html


class AdminCollectRssWidget(HiddenInput):
    """
    Widget for RssSource id
    The id is hidden and replaced by an action button calling the collect_rss_items view
    """

    def render(self, name, value, attrs=None):
        """returns html"""
        widget = super(AdminCollectRssWidget, self).render(name, value, attrs) # pylint: disable=E1002
        html = '{0}'.format(widget)
        html += value
        src_id = RssSource.objects.get(url=value).id
        url = reverse('rss_sync_collect_rss_items', args=[src_id])
        html += get_button_code(_('Collect'), url, True)
        return mark_safe(html)


class AdminCreateArticleWidget(HiddenInput):
    """
    Widget for RssItem id
    The id is hidden and replaced by an action button which is creating a CMS article
    """

    def render(self, name, value, attrs=None):
        """returns html"""
        widget = super(AdminCreateArticleWidget, self).render(name, value, attrs)  # pylint: disable=E1002
        html = '{0}'.format(widget)
        html += '{0}'.format(value)
        url = reverse('rss_sync_create_cms_article', args=[int(value)])
        html += get_button_code(_('Create CMS article'), url)
        return mark_safe(html)
