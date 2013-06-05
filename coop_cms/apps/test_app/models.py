# -*- coding: utf-8 -*-

from django.db import models
from django.core.urlresolvers import reverse

class TestClass(models.Model):
    
    field1 = models.TextField(blank=True, default="")
    field2 = models.TextField(blank=True, default="")
    other_field = models.CharField(max_length=100, blank=True, default="")

    def __unicode__(self):
        return u"Test Object {0}".format(self.id)
    
    def get_list_url(self):
        return reverse('coop_cms_testapp_list')
        
    def get_absolute_url(self):
        return reverse('coop_cms_testapp_detail', args=[self.id])
            
    def get_edit_url(self):
        return reverse('coop_cms_testapp_edit', args=[self.id])
        
    def can_view_object(self, user):
        return user.is_authenticated()
    
    def can_edit_object(self, user):
        return user.is_staff