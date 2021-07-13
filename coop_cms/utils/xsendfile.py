# -*- coding: utf-8 -*-

# Borrowed from https://bitbucket.org/wkornewald/django-filetransfers

import mimetypes

from django.conf import settings

from django.http import HttpResponse
from django.utils.encoding import smart_str

from ..settings import is_xsendfile_disabled, xsendfile_no_file_size


class ChunkedFile(object):
    def __init__(self, file):
        self.file = file

    def __iter__(self):
        return self.file.chunks()


def chunk_serve_file(request, file, save_as, content_type, **kwargs):
    """
    Serves the file in chunks for efficiency reasons, but the transfer still
    goes through Django itself, so it's much worse than using the web server,
    but at least it works with all configurations.
    """
    response = HttpResponse(ChunkedFile(file), content_type=content_type)
    if save_as:
        response['Content-Disposition'] = smart_str(u'attachment; filename={0}'.format(save_as))
    if file.size is not None:
        response['Content-Length'] = file.size
    return response


def xsendfile_serve_file(request, file, save_as, content_type, no_file_size=False, **kwargs):
    """Lets the web server serve the file using the X-Sendfile extension"""
    response = HttpResponse(content_type=content_type)
    file_path = file.name
    response['X-Sendfile'] = smart_str(file_path)
    if save_as:
        response['Content-Disposition'] = smart_str(u'attachment; filename={0}'.format(save_as))
    # Do not define a Content-Length : It may cause files not to be access correctly with XSendFile
    if not no_file_size and file.size is not None:
        response['Content-Length'] = file.size
    return response


def serve_file(request, file, backend=None, save_as=False, content_type=None):
    # Backends are responsible for handling range requests.
    filename = file.name.rsplit('/')[-1]
    if save_as is True:
        save_as = filename
    if not content_type:
        content_type = mimetypes.guess_type(filename)[0]

    if is_xsendfile_disabled():
        return chunk_serve_file(request, file, save_as=save_as, content_type=content_type)
    else:
        no_file_size = xsendfile_no_file_size()
        return xsendfile_serve_file(
            request, file, save_as=save_as, content_type=content_type, no_file_size=no_file_size
        )
