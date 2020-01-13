# -*- coding: utf-8 -*-
"""coop_bar configuration: add links to balafon"""

from django.urls import reverse
from django.utils.translation import ugettext as _

from coop_bar.utils import make_link

from coop_cms.utils import get_model_name, get_model_app, get_model_label
from .models import Emailing


def newsletters(request, context):
    """back to balafon newsletters"""
    if request and request.user.is_authenticated and request.user.is_staff:
        view_name = 'admin:{0}_{1}_changelist'.format(get_model_app(Emailing), get_model_name(Emailing))
        return make_link(
            reverse(view_name), _('Emailings'), 'table',
            classes=['icon', 'alert_on_click']
        )


def load_commands(coop_bar):
    """load commands"""
    coop_bar.register([
        [newsletters],
    ])
