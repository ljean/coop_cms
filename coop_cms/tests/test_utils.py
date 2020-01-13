# -*- coding: utf-8 -*-

from coop_cms.tests import BaseArticleTest
from coop_cms.utils import dehtml


class DehtmlTest(BaseArticleTest):
    
    def test_simple_text(self):
        text = "This is a simple text"
        self.assertEqual(dehtml(text), text)

    def test_paragraph(self):
        text = "This is a simple text"
        html_text = '<p>{0}</p>'.format(text)
        self.assertEqual(dehtml(html_text), text)

    def test_paragraph_inside(self):
        text = "<h1>This is a title</h1><p>This is a paragraph</p><p>This is another paragraph</p>"
        self.assertEqual(dehtml(text), "This is a title\n\nThis is a paragraph\n\nThis is another paragraph")

    def test_nbsp(self):
        text = "This is a simple text"
        html_text = text.replace(' ', '&nbsp;')
        self.assertNotEqual(html_text, text)
        self.assertEqual(dehtml(html_text), text)

    def test_gt_lt(self):
        text = "This is a simple text"
        html_text = '&gt;' + text + "&lt;"
        self.assertEqual(dehtml(html_text), ">" + text + "<")

    def test_special_chars(self):
        text = "This &ouml;is &auml; simple text&uuml;"
        html_text = "This &ouml;is &auml; simple text&uuml;"
        self.assertEqual(dehtml(html_text, allow_html_chars=True), text)

    def test_charset_chars(self):
        text = "à l'Opéra Grand Avignon"
        html_text = "<p>&agrave; l&#39;Op&eacute;ra Grand Avignon</p>"
        self.assertEqual(dehtml(html_text, allow_html_chars=False), text)

    def test_charset_chars_allowed(self):
        text = "&agrave; l&#39;Op&eacute;ra Grand Avignon"
        html_text = "<p>&agrave; l&#39;Op&eacute;ra Grand Avignon</p>"
        self.assertEqual(dehtml(html_text, allow_html_chars=True), text)

    def test_special_chars_two(self):
        text = "This \xf6is \xe4 simple text\xfc"
        html_text = "This &ouml;is &auml; simple text&uuml;"
        self.assertEqual(dehtml(html_text), text)
