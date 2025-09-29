# -*- coding: utf-8 -*-
"""utils"""

from .emails import send_email, send_newsletter, strip_a_tags, avoid_line_too_long, make_links_absolute  # noqa 401
from .i18n import (
    activate_lang, get_language, get_url_in_language, redirect_to_language, make_locale_path,
    strip_locale_path  # noqa 401
)
from .loaders import get_model_app, get_model_label, get_model_name, get_text_from_template  # noqa 401
from .pagination import paginate  # noqa 401
from .requests import RequestManager, RequestMiddleware, RequestNotFound  # noqa 401
from .settings import get_login_url  # noqa 401
from .text import slugify, dehtml  # noqa 401
