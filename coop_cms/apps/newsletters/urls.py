# -*- coding: utf-8 -*-

from django.conf.urls import re_path

from . import views

app_name = "newsletters"


urlpatterns = [
    re_path(
        r'^unregister/(?P<emailing_id>\d+)/(?P<contact_uuid>[\w\d-]+)/$',
        views.unregister_contact,
        name='unregister'
    ),
    re_path(
        r'^view-online/(?P<emailing_id>\d+)/(?P<contact_uuid>[\w\d-]+)/$',
        views.view_emailing_online,
        name='view_online'
    ),
    re_path(
        r'^view-online-lang/(?P<emailing_id>\d+)/(?P<contact_uuid>[\w\d-]+)/(?P<lang>\w+)/$',
        views.view_emailing_online_lang,
        name='view_online_lang'
    ),
    re_path(
        r'^link/(?P<link_uuid>[\w\d-]+)/(?P<contact_uuid>[\w\d-]+)/$',
        views.view_link,
        name='view_link'
    ),
    re_path(
        r'^email-img/(?P<emailing_id>\d+)/(?P<contact_uuid>[\w\d-]+)/$',
        views.email_tracking,
        name='email_tracking'
    ),
]
