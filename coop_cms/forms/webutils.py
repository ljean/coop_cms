# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import floppyforms.__future__ as floppyforms


class LanguageSelectionForm(floppyforms.Form):
    """Propose the different languages"""
    language = floppyforms.ChoiceField(
        label=_('Language'),
        choices=getattr(settings, 'LANGUAGES', [])
    )
