# -*- coding: utf-8 -*-
"""permission backend"""

class ArticlePermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, *args, **kwargs):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        if obj:
            field = getattr(obj, perm, None)
            if field:
                if not callable(field):
                    is_authorized = field
                else:
                    is_authorized = field(user_obj)
                return is_authorized
        return False
