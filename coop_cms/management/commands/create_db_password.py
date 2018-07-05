# -*- coding: utf-8 -*-

from getpass import getpass

from django.core.management.base import BaseCommand
from django.conf import settings

from coop_cms.secrets import set_db_password


class Command(BaseCommand):
    help = 'Generates a password DB'

    def handle(self, *args, **options):

        db_password = getpass("password?")

        set_db_password(settings.BASE_DIR, settings.SECRET_KEY, db_password)
