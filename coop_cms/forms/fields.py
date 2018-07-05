# -*- coding: utf-8 -*-
"""forms"""

from __future__ import unicode_literals

import floppyforms.__future__ as floppyforms


class HidableMultipleChoiceField(floppyforms.MultipleChoiceField):
    """
    The MultipleChoiceField doesn't return an <input type="hidden"> when hidden but an empty string
    Overload this field to restore an <input type="hidden">
    """
    hidden_widget = floppyforms.HiddenInput
