# -*- coding: utf-8 -*-
"""force sync_translation after migrate for unit tests"""

import sys

from django.conf import settings
from django.core.management import call_command
from django.core.management.commands import migrate
from django.utils.six import StringIO


class Command(migrate.Command):
    """migrate"""
    help = u"patched migrate: call sync_translation_fields after migrations when unit testing"

    def handle(self, *args, **options):
        """command"""

        super(Command, self).handle(*args, **options)

        # Unit testing force sync_translation_fields
        if 'test' in sys.argv and 'modeltranslation' in settings.INSTALLED_APPS:
            print("Call sync_translation_fields")
            sys_stdout = sys.stdout  # keep for restoring
            silent_stdout = StringIO()
            sys.stdout = silent_stdout  # make the command silent
            call_command('sync_translation_fields', interactive=False, stdout=silent_stdout)
            sys.stdout = sys_stdout  # restore stdout
