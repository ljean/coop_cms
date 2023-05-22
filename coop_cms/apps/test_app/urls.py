# -*- coding: utf-8 -*-
"""for unit-testing"""

from django.urls import path

from . import views


urlpatterns = [
    path('coop-cms-testclass/', views.TestClassListView.as_view(), name='coop_cms_testapp_list'),
    path('works/<int:pk>/cms_edit/', views.TestClassEditView.as_view(), name='coop_cms_testapp_edit'),
    path('works/<int:pk>/', views.TestClassDetailView.as_view(), name='coop_cms_testapp_detail'),
    path('works/cms_edit/', views.TestClassFormsetEditView.as_view(), name='coop_cms_testapp_formset_edit'),
    path('works/', views.TestClassFormsetView.as_view(), name='coop_cms_testapp_formset'),
]
