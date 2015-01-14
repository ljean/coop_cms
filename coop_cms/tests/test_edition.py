# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from bs4 import BeautifulSoup
from django.template import Template, Context

from model_mommy import mommy

from coop_cms.models import PieceOfHtml
from coop_cms.settings import get_article_class
from coop_cms.tests import BaseTestCase, BaseArticleTest


class PieceOfHtmlTagsTest(BaseTestCase):
    
    def test_create_poc(self):
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({}))
        self.assertEqual(html, "")
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_existing_poc(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_create_poc_read_only(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" read-only %}')
        html = tpl.render(Context({}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_create_edit_poc(self):
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertNotEqual(html, "")
        
        soup = BeautifulSoup(html)
        tags = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].text, "")
        
        tags_hidden = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content_hidden")
        self.assertEqual(len(tags_hidden), 1)
        self.assertEqual(tags_hidden[0].get("value", ""), "")
        
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_edit_poc(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertNotEqual(html, poc.content)
        
        soup = BeautifulSoup(html)
        tags = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].text, poc.content)
        
        tags_hidden = soup.select("#djaloha_djaloha__coop_cms__PieceOfHtml__div_id__test__content_hidden")
        self.assertEqual(len(tags_hidden), 1)
        self.assertEqual(tags_hidden[0]["value"], poc.content)
        
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_edit_poc_read_only(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" read-only %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        
    def test_view_poc_extra_id(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!", extra_id="1")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" extra_id=1 %}')
        html = tpl.render(Context({"djaloha_edit": False}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        self.assertEqual(poc.extra_id, "1")
        
    def test_edit_poc_extra_id(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!", extra_id="1")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" extra_id=1 %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        
        soup = BeautifulSoup(html)
        #print html
        tags = soup.select("input[type=hidden]")
        self.assertEqual(len(tags), 1)
        div_selector = tags[0].attrs['id']
        div_selector = div_selector.replace("_hidden", "")
        
        tags = soup.select("#"+div_selector)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].text, poc.content)
        
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        self.assertEqual(poc.extra_id, "1")
        
    def test_create_poc_extra_id(self):
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" extra_id=1 %}')
        html = tpl.render(Context({"djaloha_edit": False}))
        self.assertEqual(html, "")
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        poc = PieceOfHtml.objects.all()[0]
        self.assertEqual(poc.div_id, "test")
        self.assertEqual(poc.extra_id, "1")
        
    def test_create_new_poc_extra_id(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!", extra_id="1")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" extra_id=2 %}')
        html = tpl.render(Context({"djaloha_edit": False}))
        self.assertEqual(html, "")
        self.assertEqual(PieceOfHtml.objects.count(), 2)
        PieceOfHtml.objects.get(div_id="test", extra_id="1")
        PieceOfHtml.objects.get(div_id="test", extra_id="2")
        
    def test_poc_extra_id_readonly(self):
        poc = mommy.make(PieceOfHtml, div_id="test", content="HELLO!!!", extra_id="1")
        tpl = Template('{% load coop_edition %}{% coop_piece_of_html "test" read-only extra_id=1 %}')
        html = tpl.render(Context({"djaloha_edit": True}))
        self.assertEqual(html, poc.content)
        self.assertEqual(PieceOfHtml.objects.count(), 1)
        PieceOfHtml.objects.get(div_id="test", extra_id="1")


class BlockInheritanceTest(BaseArticleTest):

    def setUp(self):
        super(BlockInheritanceTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article_with_blocks.html', 'Article with blocks'),
        )

    def tearDown(self):
        super(BlockInheritanceTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates

    def test_view_with_blocks(self):
        Article = get_article_class()
        a = mommy.make(
            Article,
            title=u"This is my article", content=u"<p>This is my <b>content</b></p>",
            template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        )

        response = self.client.get(a.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, a.title)
        self.assertContains(response, a.content)

        self.assertContains(response, "*** HELLO FROM CHILD ***")
        self.assertContains(response, "*** HELLO FROM PARENT ***")
        self.assertContains(response, "*** HELLO FROM BLOCK ***")

    def test_edit_with_blocks(self):
        Article = get_article_class()
        a = mommy.make(
            Article,
            title=u"This is my article", content=u"<p>This is my <b>content</b></p>",
            template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        )

        self._log_as_editor()

        data = {
            "title": u"This is a new title",
            'content': "<p>This is a <i>*** NEW ***</i> <b>content</b></p>"
        }
        response = self.client.post(a.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        a = Article.objects.get(id=a.id)

        self.assertEqual(a.title, data['title'])
        self.assertEqual(a.content, data['content'])

        self.assertContains(response, a.title)
        self.assertContains(response, a.content)

        self.assertContains(response, "*** HELLO FROM CHILD ***")
        self.assertContains(response, "*** HELLO FROM PARENT ***")
        self.assertContains(response, "*** HELLO FROM BLOCK ***")

