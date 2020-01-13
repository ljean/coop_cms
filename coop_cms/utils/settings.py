# -*- coding: utf-8 -*-
"""utils"""

from coop_cms.moves import reverse, NoReverseMatch


def get_login_url():
    """returns the URL of the login page"""
    try:
        return reverse("auth_login")
    except NoReverseMatch:
        return reverse("login")

