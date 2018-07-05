# -*- coding: utf-8 -*-
"""utils"""

from __future__ import unicode_literals

from django.core.urlresolvers import reverse, NoReverseMatch


def get_login_url():
    """returns the URL of the login page"""
    try:
        return reverse("auth_login")
    except NoReverseMatch:
        return reverse("login")

