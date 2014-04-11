# -*- coding: utf-8 -*-

from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse, NoReverseMatch

class PermissionsMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied) and (not request.user.is_authenticated()):
            try:
                login_url = reverse('auth_login')
            except NoReverseMatch:
                try:
                    login_url = reverse('login')
                except NoReverseMatch:
                    login_url = None
            return redirect_to_login(request.path, login_url)
        