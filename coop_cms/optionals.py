# -*- coding: utf-8 -*-
"""Every code which depends from optional apps"""

from django.conf import settings


def not_implemented(*args, **kwargs):
    raise NotImplemented


if 'modeltranslation' in settings.INSTALLED_APPS:
    from modeltranslation.utils import build_localized_fieldname
else:
    build_localized_fieldname = lambda x, y: x


if 'wkhtmltopdf' in settings.INSTALLED_APPS:
    from wkhtmltopdf.utils import convert_to_pdf, make_absolute_paths
    from wkhtmltopdf.views import PDFResponse
else:
    convert_to_pdf = not_implemented
    make_absolute_paths = not_implemented
    PDFResponse = not_implemented