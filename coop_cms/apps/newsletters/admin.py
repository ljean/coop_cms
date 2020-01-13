# -*- coding: utf-8 -*-
"""admin site"""

from django.contrib import admin

import floppyforms.__future__ as forms

from . import models
from . import settings


@admin.register(models.Emailing)
class EmailingAdmin(admin.ModelAdmin):
    """Emailing"""
    list_display = ['newsletter', 'creation_dt', 'subscription_type', 'status']
    list_editable = ['status']
    raw_id_fields = [
        'send_to', 'sent_to', 'opened_emails', 'unsub',
    ]
    search_fields = ['newsletter__subject', 'newsletter__content']
    list_filter = ['status', 'subscription_type']
    date_hierarchy = 'creation_dt'


@admin.register(models.MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    """Magic link"""
    list_display = ['url', 'emailing']
    search_fields = ['url', 'emailing']
    raw_id_admin = ('emailing',)


@admin.register(models.SubscriptionType)
class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'site', 'order_index', )

    def get_form(self, *args, **kwargs):
        form_class = super().get_form(*args, **kwargs)

        class custom_form_class(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['lang'].widget = forms.Select(choices=settings.get_language_choices())

        return custom_form_class


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscription_type', 'contact', )
    raw_id_fields = ('subscription_type', 'contact', )


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'email_verified')
