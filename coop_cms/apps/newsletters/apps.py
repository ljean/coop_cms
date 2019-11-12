from django.apps import AppConfig as BaseAppConfig

from django.utils.translation import ugettext_lazy as _


class AppConfig(BaseAppConfig):
    name = 'coop_cms.apps.newsletters'
    verbose_name = _("Newsletters")

