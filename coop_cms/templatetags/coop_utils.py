# -*- coding: utf-8 -*-

from coop_cms.settings import get_article_class
from coop_cms.utils import get_article
from django import template
register = template.Library()
from django.template.defaultfilters import slugify
from coop_cms.utils import dehtml as do_dehtml
from bs4 import BeautifulSoup
import unicodedata
    
################################################################################
class ArticleLinkNode(template.Node):

    def __init__(self, title, lang):
        self.title = title
        self.lang = lang

    def render(self, context):
        Article = get_article_class()
        
        try:
            v = template.Variable(self.title)
            title = v.resolve(context)
        except template.VariableDoesNotExist:
            title = self.title.strip("'").strip('"')
        
        slug = slugify(title)
        try:
            if self.lang:
                article = get_article(slug, force_lang=self.lang)
            else:
                #If the language is not defined, we need to get it from the context
                #The get_language api doesn't work in templatetag
                request = context['request']
                article = get_article(slug, current_lang=request.LANGUAGE_CODE)
            
        except Article.DoesNotExist:
            article = Article.objects.create(slug=slug, title=title)
        
        return article.get_absolute_url()

@register.tag
def article_link(parser, token):
    args = token.split_contents()
    title = args[1]
    lang = args[2] if len(args) > 2 else None
    return ArticleLinkNode(title, lang)

@register.filter
def dehtml(value):
    return do_dehtml(value)
    
@register.filter
def sp_rt_lb(value):
    return value.replace("\n", " ").replace("\r", "")
    
################################################################################
class NewsletterFriendlyCssNode(template.Node):

    def __init__(self, nodelist_content, css):
        self.css = css
        self.nodelist_content = nodelist_content

    def render(self, context):
        content = self.nodelist_content.render(context)
        if context.get('by_email', False):
            soup = BeautifulSoup(content)
            for tag, css in self.css.items():
                for html_tag in soup.select(tag):
                    html_tag["style"] = css
            content = soup.prettify(formatter="minimal")
        else:
            style = ""
            for tag, value in self.css.items():
                style += u"{0} {{ {1} }}\n".format(tag, value)
            content = u"<style>\n{0}</style>\n".format(style) + content
        return content

@register.tag
def nlf_css(parser, token):
    #Newsletter friendly CSS
    args = token.split_contents()
    css = {}
    for item in args[1:]:
        tag, value = item.split("=")
        tag, value = tag.strip('"'), value.strip('"')
        css[tag] = value
    nodelist = parser.parse(('end_nlf_css',))
    token = parser.next_token()
    return NewsletterFriendlyCssNode(nodelist, css)

@register.filter
def normalize_utf8_to_ascii(ustr):
    try:
        return unicodedata.normalize('NFKD', ustr).encode('ascii','ignore')
    except TypeError:
        return ustr
    