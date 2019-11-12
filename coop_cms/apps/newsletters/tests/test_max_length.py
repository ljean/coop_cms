# -*- coding: utf-8 -*-
"""test email sending"""

from coop_cms.tests import BaseTestCase

from ..utils import force_line_max_length


class MaxLineLengthTest(BaseTestCase):
    """Check that we can control the max length of line"""

    def test_force_line_max_length(self):
        """it should not have a line more than 400 chars"""

        in_lines = [
            'This is a messsage',
            "123456789 " * 50,
            "That's all folks!"
        ]
        text = "\n".join(in_lines)

        out_text = force_line_max_length(text, max_length_per_line=400, dont_cut_in_quotes=True)
        out_lines = out_text.split("\n")

        self.assertEqual(len(out_lines), 4)
        self.assertEqual(out_lines[0], in_lines[0])
        self.assertEqual(out_lines[1], "123456789 " * 40 + "123456789")
        self.assertEqual(out_lines[2], "123456789 " * 8 + "123456789")
        self.assertEqual(out_lines[3], in_lines[2])

    def test_force_line_max_length_in_p(self):
        """it should not have a line more than 400 chars"""

        content = """
            <html>
            <body>
            </body>
            <h1>Title</h1>
            <p>
                Paragraph1
                Ok
            </p>
            <p>Paragraph 2</p>
            <p>{0}</p>
            </html>
        """.format("123456789 " * 50)

        expected_content = """
            <html>
            <body>
            </body>
            <h1>Title</h1>
            <p>
                Paragraph1
                Ok
            </p>
            <p>Paragraph 2</p>\n<p>{0}\n{1}</p>
            </html>
        """.format(
            "123456789 " * 39 + "123456789",
            "123456789 " * 10
        )

        result = force_line_max_length(content, max_length_per_line=400, dont_cut_in_quotes=False)
        self.assertEqual(expected_content, result)

    def test_force_line_max_length_a1(self):
        """it should not have a line more than 400 chars"""

        content = """
            <html>
            <body>
            </body>
            <h1>Title</h1>
            <p>
                Paragraph1
                Ok
            </p>
            <p>Paragraph 2</p>
            <p>{0}<a href="{1}">This is a link</a></p>
            </html>
        """.format("123456789 " * 36, "this-is-a-link-dont-cut-in-quotes")

        expected_content = """
            <html>
            <body>
            </body>
            <h1>Title</h1>
            <p>
                Paragraph1
                Ok
            </p>
            <p>Paragraph 2</p>\n<p>{0}<a href="{1}">This\nis a link</a></p>
            </html>
        """.format("123456789 " * 36, "this-is-a-link-dont-cut-in-quotes")

        result = force_line_max_length(content,  max_length_per_line=400, dont_cut_in_quotes=False)

        self.assertEqual(expected_content, result)

    def test_force_line_max_length_a2(self):
        """it should not have a line more than 400 chars"""

        content = """
            <html>
            <body>
            </body>
            <h1>Title</h1>
            <p>
                Paragraph1
                Ok
            </p>
            <p>Paragraph 2</p>
            <p>{0}<a class="abcdefgh ijklmnop qrstuvwxyz" href="{1}">This is a link</a></p>
            </html>
        """.format("123456789 " * 38, "this-is-a-link-dont-cut-in-quotes")

        expected_content = """
            <html>
            <body>
            </body>
            <h1>Title</h1>
            <p>
                Paragraph1
                Ok
            </p>
            <p>Paragraph 2</p>\n<p>{0}<a class="abcdefgh ijklmnop qrstuvwxyz"\nhref="{1}">This is a link</a></p>
            </html>
        """.format("123456789 " * 38, "this-is-a-link-dont-cut-in-quotes")

        result = force_line_max_length(content, max_length_per_line=400, dont_cut_in_quotes=False)
        self.assertEqual(expected_content, result)
