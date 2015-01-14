# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from django.core.urlresolvers import reverse

from model_mommy import mommy

from coop_cms.settings import get_article_class
from coop_cms.tests import BaseArticleTest


class TemplateTest(BaseArticleTest):
    
    def setUp(self):
        super(TemplateTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('coop_cms/article.html', 'coop_cms base article'),
            ('test/article.html', 'test article'),
        )
        
    def tearDown(self):
        super(TemplateTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates

    def test_view_article(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertTemplateUsed(response, 'coop_cms/article.html')
        self.assertEqual(200, response.status_code)
        
    def test_view_article_custom_template(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass, publication=klass.PUBLISHED, template='test/article.html')
        response = self.client.get(article.get_absolute_url())
        self.assertTemplateUsed(response, 'test/article.html')
        self.assertEqual(200, response.status_code)
        
    def test_change_template(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass)
        self._log_as_editor()
        url = reverse('coop_cms_change_template', args=[article.id])
        response = self.client.post(url, data={'template': 'test/article.html'}, follow=True)
        self.assertEqual(200, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.template, 'test/article.html')
        
    def test_change_template_permission(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make(klass)
        url = reverse('coop_cms_change_template', args=[article.id])
        response = self.client.post(url, data={'template': 'test/article.html'}, follow=True)
        self.assertEqual(200, response.status_code)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.template, '')


