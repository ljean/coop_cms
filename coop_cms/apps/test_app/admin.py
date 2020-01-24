# -*- coding: utf-8 -*-
"""admin"""

from django.contrib import admin
from coop_cms.apps.test_app import models


@admin.register(models.TestClass)
class TestClassAdmin(admin.ModelAdmin):
    pass
