# -*- coding: utf-8 -*-

from django.urls import path

from . import views

app_name = "newsletters"


urlpatterns = [
    path(
        'unregister/<int:emailing_id>/<uuid:contact_uuid>/',
        views.unregister_contact,
        name='unregister'
    ),
    path(
        'view-online/<int:emailing_id>/<uuid:contact_uuid>/',
        views.view_emailing_online,
        name='view_online'
    ),
    path(
        'view-online-lang/<int:emailing_id>/<uuid:contact_uuid>/<str:lang>/',
        views.view_emailing_online_lang,
        name='view_online_lang'
    ),
    path(
        'link/<uuid:link_uuid>/<uuid:contact_uuid>/',
        views.view_link,
        name='view_link'
    ),
    path(
        'email-img/<int:emailing_id>/<uuid:contact_uuid>/',
        views.email_tracking,
        name='email_tracking'
    ),
]
