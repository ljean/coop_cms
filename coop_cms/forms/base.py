# -*- coding: utf-8 -*-
"""forms"""

import floppyforms as floppyforms

from coop_html_editor.settings import init_url, ckeditor_version
from coop_html_editor.widgets import CkEditorInput, Media, logging


class CoopCkEditorInput(CkEditorInput):

    def __init__(self, kind, *args, **kwargs):
        self.kind = kind
        super().__init__(*args, **kwargs)

    @property
    def media(self):
        try:
            css = {'all': ()}
            js_files = [
                '{0}/ckeditor.js'.format(ckeditor_version()),
                init_url() + ('?kind=' + self.kind if self.kind else ''),
            ]
            return Media(css=css, js=js_files)
        except Exception as msg:
            django_logger = logging.getLogger('django')
            django_logger.error(u'CkEditorInput._get_media Error {0}'.format(msg))


class InlineHtmlEditableModelForm(floppyforms.ModelForm):
    """Base class for form with inline-HTML editor fields"""
    is_inline_editable = True  # The cms_edition templatetag checks this for switching to edit mode
    kind = ''

    def __init__(self, *args, **kwargs):
        super(InlineHtmlEditableModelForm, self).__init__(*args, **kwargs)  # pylint: disable=E1002
        for field_name in self.Meta.fields:
            no_inline_html_widgets = getattr(self.Meta, 'no_inline_editable_widgets', ())
            if field_name not in no_inline_html_widgets:
                self.fields[field_name].widget = CoopCkEditorInput(self.kind)

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
