from django.apps import AppConfig as BaseAppConfig

from django.utils.translation import gettext_lazy as _


class AppConfig(BaseAppConfig):
    name = 'coop_cms.apps.newsletters'
    verbose_name = _("Newsletters")
