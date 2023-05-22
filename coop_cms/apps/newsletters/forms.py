# -*- coding: utf-8 -*-
"""forms"""

from django.utils.translation import gettext_lazy as _

import floppyforms as forms

from ...bs_forms import Form as BsForm


class UnregisterForm(BsForm):
    """User wants to unregister from emailing"""
    reason = forms.CharField(required=False, widget=forms.Textarea, label=_("Reason"))
