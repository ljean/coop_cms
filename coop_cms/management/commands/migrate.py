# -*- coding: utf-8 -*-
"""send newsletter"""

from __future__ import unicode_literals

import sys

from django.conf import settings
from django.core.management import call_command
from django.core.management.commands import migrate


class Command(migrate.Command):
    """force sync_translation_fields when migrating test database if modeltrnaslation is installed"""
    help = "migrate"
    # use_argparse = False

    def handle(self, *args, **options):
        """command"""

        super(Command, self).handle(*args, **options)
        if 'test' in sys.argv and 'modeltranslation' in settings.INSTALLED_APPS:
            call_command('sync_translation_fields', interactive=False)
