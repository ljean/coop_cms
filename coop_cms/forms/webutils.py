# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import floppyforms


class LanguageSelectionForm(floppyforms.Form):
    """Propose the different languages"""
    language = floppyforms.ChoiceField(
        label=_(u'Language'),
        choices=getattr(settings, 'LANGUAGES', [])
    )