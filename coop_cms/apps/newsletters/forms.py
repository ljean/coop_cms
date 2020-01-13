# -*- coding: utf-8 -*-
"""forms"""

from django.utils.translation import ugettext_lazy as _

from coop_cms.bs_forms import Form as BsForm
import floppyforms.__future__ as forms


class UnregisterForm(BsForm):
    """User wants to unregister from emailing"""
    reason = forms.CharField(required=False, widget=forms.Textarea, label=_("Reason"))
