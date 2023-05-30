# -*- coding:utf-8 -*-
"""urls"""

from django.conf import settings
from django.urls import include, path, re_path

from . import sitemap
from .settings import (
    get_article_views, install_csrf_failure_view, change_site_domain
)
from .views.newsletters import NewsletterView, NewsletterPdfView
from .views import articles, fragments, homepage, links, navigation, newsletters, medialib, webutils
from .views.webutils import DebugErrorCodeView

article_views = get_article_views()
article_view = article_views['article_view']
edit_article_view = article_views['edit_article_view']

install_csrf_failure_view()
change_site_domain()


urlpatterns = [
    path('htm-editor/', include('coop_html_editor.urls')),

    path('cms/change-template/<int:article_id>/', articles.change_template, name="coop_cms_change_template"),
    path('cms/settings/<int:article_id>/', articles.article_settings, name="coop_cms_article_settings"),
    path('cms/new/', articles.new_article, name="coop_cms_new_article"),
    path('cms/new/article/', articles.new_article, name="coop_cms_new_article"),
    path('cms/update-logo/<int:article_id>/', articles.update_logo, name="coop_cms_update_logo"),
    path('cms/articles/', articles.view_all_articles, name="coop_cms_view_all_articles"),
    path('cms/', articles.view_all_articles),
    path('articles/<slug:slug>/', articles.ArticlesByCategoryView.as_view(), name="coop_cms_articles_category"),

    path('cms/fragments/add/', fragments.add_fragment, name='coop_cms_add_fragment'),
    path('cms/fragments/edit/', fragments.edit_fragments, name='coop_cms_edit_fragments'),

    path('cms/set-homepage/<int:article_id>)/', homepage.set_homepage, name='coop_cms_set_homepage'),

    path('cms/new/link/', links.new_link, name="coop_cms_new_link"),

    path('cms/tree/<int:tree_id>/', navigation.process_nav_edition, name='navigation_tree'),

    path('cms/newsletter/new/', newsletters.newsletter_settings, name='coop_cms_new_newsletter'),
    path(
        'cms/newsletter/settings/<int:newsletter_id>/',
        newsletters.newsletter_settings,
        name='coop_cms_newsletter_settings'
    ),
    path(
        'cms/newsletter/<int:id>/',
        NewsletterView.as_view(),
        name='coop_cms_view_newsletter'
    ),
    path(
        'cms/newsletter-pdf/<int:id>/',
        NewsletterPdfView.as_view(),
        name='coop_cms_newsletter_pdf'
    ),
    path(
        'cms/newsletter/<int:id>/cms_edit/',
        NewsletterView.as_view(edit_mode=True),
        name='coop_cms_edit_newsletter'
    ),
    path(
        'cms/newsletter/change-template/<int:newsletter_id>/',
        newsletters.change_newsletter_template,
        name="coop_cms_change_newsletter_template"
    ),
    path(
        'cms/newsletter/test/<int:newsletter_id>/',
        newsletters.test_newsletter,
        name="coop_cms_test_newsletter"
    ),
    path(
        'cms/newsletter/schedule/<int:newsletter_id>/',
        newsletters.schedule_newsletter_sending,
        name="coop_cms_schedule_newsletter_sending"
    ),

    path('cms/media-images/', medialib.show_media, {'media_type': 'image'}, name='coop_cms_media_images'),
    path('cms/media-documents/', medialib.show_media, {'media_type': 'document'}, name='coop_cms_media_documents'),
    path(
        'cms/media-photologue/',
        medialib.show_media,
        {'media_type': 'photologue'},
        name='coop_cms_media_photologue'
    ),
    path('cms/upload-image/', medialib.upload_image, name="coop_cms_upload_image"),
    path('cms/upload-doc/', medialib.upload_doc, name="coop_cms_upload_doc"),
    path('cms/private-download/<int:doc_id>/', medialib.download_doc, name='coop_cms_download_doc'),

    path('cms/change-language/', webutils.change_language, name='coop_cms_change_language'),
    path('cms/swicth-language/', webutils.switch_language_popup, name='coop_cms_switch_language_popup'),

    path(
        'cms/accept-cookies-message/',
        webutils.accept_cookies_message,
        name='coop_cms_accept_cookies_message'
    ),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r'^cms/debug-error-code/(?P<error_code>\d{3})/$',
            DebugErrorCodeView.as_view(),
            name='coop_cms_debug_404'
        ),
    ]

if not getattr(settings, "COOP_CMS_DISABLE_DEFAULT_SITEMAP", False):
    urlpatterns += sitemap.urlpatterns

if 'coop_cms.apps.rss_sync' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('rss-sync/', include('coop_cms.apps.rss_sync.urls')),
    ]

if 'coop_cms.apps.test_app' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('this-should-be-only-in-test-mode', include('coop_cms.apps.test_app.urls')),
    ]

# keep these at the end
urlpatterns += [
    re_path(r'(?P<url>[-\w]+)/cms_publish/$', articles.publish_article, name='coop_cms_publish_article'),
    re_path(r'^(?P<url>[-\w]+)/cms_cancel/$', articles.cancel_edit_article, name='coop_cms_cancel_edit_article'),
    path('', homepage.homepage, name='coop_cms_homepage'),
    re_path(r'^(?P<slug>[-\w]+)/cms_edit/$', edit_article_view.as_view(edit_mode=True), name='coop_cms_edit_article'),
    re_path(r'^(?P<slug>[-\w]+)/$', article_view.as_view(), name='coop_cms_view_article'),
    re_path(r'^(?P<path>.+)$', articles.AliasView.as_view(), name='coop_cms_view_alias'),
    path('coop_bar/', include('coop_bar.urls')),
]
