# -*- coding: utf-8 -*-
"""models"""

from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible


class TestTag(models.Model):
    """for unit-testing : test_view_object_m2m_relationships"""
    name = models.CharField(max_length=100)


@python_2_unicode_compatible
class TestClass(models.Model):
    """for unit-testing"""

    field1 = models.TextField()
    field2 = models.TextField()
    field3 = models.CharField(max_length=100, blank=True)
    bool_field = models.BooleanField(default=False)
    int_field = models.IntegerField(default=0)
    float_field = models.FloatField(default=0.0)

    other_field = models.CharField(max_length=100)

    tags = models.ManyToManyField(TestTag, blank=True)

    def __str__(self):
        return "Test Object {0}".format(self.id)

    def get_list_url(self):
        """for unit-testing"""
        return reverse('coop_cms_testapp_list')

    def get_absolute_url(self):
        """for unit-testing"""
        return reverse('coop_cms_testapp_detail', args=[self.id])

    def get_edit_url(self):
        """for unit-testing"""
        return reverse('coop_cms_testapp_edit', args=[self.id])

    def can_view_object(self, user):
        """for unit-testing"""
        return user.is_authenticated()

    def can_edit_object(self, user):
        """for unit-testing"""
        return user.is_staff

    @property
    def properties(self):
        """for unit-testing"""
        return {"abc": "ABC"}
