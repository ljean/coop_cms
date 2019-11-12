# -*- coding: utf-8 -*-

# from django.contrib.auth.models import User

# from coop_cms.tests import BaseTestCase as CoopCmsBaseTestCase
#
#
# class BaseTestCase(CoopCmsBaseTestCase):
#
#     def setUp(self):
#         super(BaseTestCase, self).setUp()
#         self.user = User.objects.create(username="toto")
#         self.user.set_password("abc")
#         self.user.is_staff = True
#         self.user.save()
#         self._login()
#
#     def _login(self):
#         return self.client.login(username="toto", password="abc")