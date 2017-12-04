# -*- coding: utf-8 -*-

from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

from ...models import InvalidatedUser


class Command(BaseCommand):
    help = u"send waiting messages by emails to the doctors"

    def handle(self, *args, **options):
        # look for emailing to be sent
        for user in User.objects.all():
            password = get_random_string(length=12)
            user.set_password(password)
            user.save()

            InvalidatedUser.objects.create(
                user=user,
                invalidation_datetime=datetime.now()
            )
