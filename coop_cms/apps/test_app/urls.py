# -*- coding: utf-8 -*-
"""for unit-testing"""

from django.conf.urls import url

from coop_cms.apps.test_app import views


urlpatterns = [
    url(r'^coop-cms-testclass/$', views.TestClassListView.as_view(), name='coop_cms_testapp_list'),
    url(r'^works/(?P<pk>\d+)/cms_edit$', views.TestClassEditView.as_view(), name='coop_cms_testapp_edit'),
    url(r'^works/(?P<pk>\d+)/$', views.TestClassDetailView.as_view(), name='coop_cms_testapp_detail'),
    url(r'^works/cms_edit/$', views.TestClassFormsetEditView.as_view(), name='coop_cms_testapp_formset_edit'),
    url(r'^works/$', views.TestClassFormsetView.as_view(), name='coop_cms_testapp_formset'),
]
