# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
import views

urlpatterns = patterns('', 
    url(r'^coop-cms-testclass/$', views.TestClassListView.as_view(), name='coop_cms_testapp_list'),
    url(r'^works/(?P<pk>\d+)/cms_edit$', views.TestClassEditView.as_view(), name='coop_cms_testapp_edit'),
    url(r'^works/(?P<pk>\d+)/$', views.TestClassDetailView.as_view(), name='coop_cms_testapp_detail'),
)