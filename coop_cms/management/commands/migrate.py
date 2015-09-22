# -*- coding: utf-8 -*-
"""send newsletter"""

import sys

from django.core.management.commands import migrate
from django.core.management import call_command

class Command(migrate.Command):
    """send newsletter"""
    help = u"migrate"
    #use_argparse = False

    def handle(self, *args, **options):
        """command"""
        super(Command, self).handle(*args, **options)
        if 'test' in sys.argv:
            call_command('sync_translation_fields', interactive=False)
