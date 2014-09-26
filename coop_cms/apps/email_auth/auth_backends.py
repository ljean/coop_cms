# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

class EmailAuthBackend(ModelBackend):
    def authenticate(self, email=None, password=None, **kwargs):
        email = email.strip() if email else email
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                return None
            
            if not user.is_active:
                return None
            
            if user.check_password(password):
                return user
            
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            for u in User.objects.filter(email=email):
                if u.check_password(password):
                    return u
            return None