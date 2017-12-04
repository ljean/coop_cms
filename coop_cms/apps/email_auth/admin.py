# -*- coding: utf-8 -*-
"""Use email rather than username for user authentication"""

from django.contrib import admin

from .models import InvalidatedUser


class InvalidatedUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'password_changed', )
    list_filter = ('password_changed', )
    date_hierarchy = 'invalidation_datetime'
    search_fields = ('user__email', )

admin.site.register(InvalidatedUser, InvalidatedUserAdmin)
