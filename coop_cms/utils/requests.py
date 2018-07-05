# -*- coding: utf-8 -*-
"""utils"""

from __future__ import unicode_literals

from threading import current_thread

from coop_cms.moves import MiddlewareMixin


class RequestNotFound(Exception):
    """exception"""
    pass


class RequestManager(object):
    """get django request from anywhere"""
    _shared = {}

    def __init__(self):
        """his is a Borg"""
        self.__dict__ = RequestManager._shared

    def _get_request_dict(self):
        """request dict"""
        if not hasattr(self, '_request'):
            self._request = {}  # pylint: disable=attribute-defined-outside-init
        return self._request

    def clean(self):
        """clean"""
        if hasattr(self, '_request'):
            del self._request

    def get_request(self):
        """return request"""
        _requests = self._get_request_dict()
        the_thread = current_thread()
        if the_thread not in _requests:
            raise RequestNotFound("Request not found: make sure that middleware is installed")
        return _requests[the_thread]

    def set_request(self, request):
        """set request"""
        _requests = self._get_request_dict()
        _requests[current_thread()] = request


class RequestMiddleware(MiddlewareMixin):
    """middleware for request"""

    def process_request(self, request):
        """middleware is called before every request"""
        RequestManager().set_request(request)

    def process_response(self, request, response):
        """process response"""
        # Clear the request : avoid error in unit tests
        RequestManager().set_request(None)
        return response
