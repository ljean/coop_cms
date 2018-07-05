# -*- coding: utf-8 -*-
"""utils"""

from .emails import send_email, send_newsletter, strip_a_tags, avoid_line_too_long, make_links_absolute
from .i18n import (
    activate_lang, get_language, get_url_in_language, redirect_to_language, make_locale_path, strip_locale_path
)
from .loaders import get_model_app, get_model_label, get_model_name, get_text_from_template
from .pagination import paginate
from .requests import RequestManager, RequestMiddleware, RequestNotFound
from .settings import get_login_url
from .text import slugify, dehtml
