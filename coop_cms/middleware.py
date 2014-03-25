# -*- coding: utf-8 -*-

from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

class PermissionsMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied) and (not request.user.is_authenticated()):
            return redirect_to_login(request.path)
        