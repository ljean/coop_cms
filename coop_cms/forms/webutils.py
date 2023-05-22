# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import gettext_lazy as _

import floppyforms as floppyforms


class LanguageSelectionForm(floppyforms.Form):
    """Propose the different languages"""
    language = floppyforms.ChoiceField(
        label=_('Language'),
        choices=getattr(settings, 'LANGUAGES', [])
    )
