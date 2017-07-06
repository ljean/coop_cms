# -*- coding: utf-8 -*-
"""forms"""

from __future__ import unicode_literals

import floppyforms.__future__ as floppyforms

from coop_html_editor.widgets import get_inline_html_widget


class InlineHtmlEditableModelForm(floppyforms.ModelForm):
    """Base class for form with inline-HTML editor fields"""
    is_inline_editable = True  # The cms_edition templatetag checks this for switching to edit mode

    def __init__(self, *args, **kwargs):
        super(InlineHtmlEditableModelForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        for field_name in self.Meta.fields:
            no_inline_html_widgets = getattr(self.Meta, 'no_inline_editable_widgets', ())
            if field_name not in no_inline_html_widgets:
                self.fields[field_name].widget = get_inline_html_widget()

    class Media:
        css = {
            'all': ('css/colorbox.css', ),
        }
        js = (
            'js/jquery.form.js',
            'js/jquery.pageslide.js',
            'js/jquery.colorbox-min.js',
            'js/colorbox.coop.js',
        )
