# -*- coding: utf-8 -*-
"""urls"""

from __future__ import unicode_literals

import sys

from django.conf import settings
from django.urls import include, re_path, path
from django.contrib import admin
from django.contrib.staticfiles.views import serve as serve_static
from django.views.static import serve as serve_media

from coop_cms.settings import get_url_patterns, get_media_root

localized_patterns = get_url_patterns()

urlpatterns = []

if settings.DEBUG or ('test' in sys.argv) or getattr(settings, 'SERVE_STATIC', True):
    if settings.DEBUG:
        urlpatterns += [
            re_path(r'^static/(?P<path>.*)$', serve_static),
        ]
    else:
        urlpatterns += [
            re_path(r'^static/(?P<path>.*)$', serve_media, {'document_root': settings.STATIC_ROOT}),
        ]
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve_media,
            {'document_root': get_media_root(), 'show_indexes': True}
        ),
    ]

urlpatterns += localized_patterns(
    # path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('coop_cms.apps.email_auth.urls')),
    # path('accounts/', include('coop_cms.apps.email_auth.registration_backend.urls')),
    # path('accounts/', include('registration.backends.model_activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('coop_cms.urls')),
)
