# -*- coding: utf-8 -*-
"""admin"""

from django.contrib import admin

from . import models


@admin.register(models.TestClass)
class TestClassAdmin(admin.ModelAdmin):
    pass
