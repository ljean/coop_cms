# -*- coding: utf-8 -*-
"""common place for settings. Define defaults"""

from django.utils.translation import ugettext as _
from django.conf import settings as project_settings


def get_language_choices(default_label=None):
    """returns list of languages"""
    if default_label is None:
        default_label = _('Default')
    return [('', default_label)] + list(project_settings.LANGUAGES)


def has_language_choices():
    """returns true if we should propose language choices"""
    return len(project_settings.LANGUAGES) >= 2
