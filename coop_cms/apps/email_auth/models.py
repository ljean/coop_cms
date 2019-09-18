# -*- coding: utf-8 -*-
"""models"""

from django.contrib.auth.models import User
from django.db import models


class InvalidatedUser(models.Model):
    """Show a message for these users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password_changed = models.BooleanField(default=False)
    invalidation_datetime = models.DateTimeField()

    def __unicode__(self):
        return u'{0}'.format(self.user.email)
