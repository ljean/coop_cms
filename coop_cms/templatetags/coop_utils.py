# -*- coding: utf-8 -*-

from coop_cms.settings import get_article_class
from django import template
register = template.Library()
from django.template.defaultfilters import slugify

################################################################################
class ArticleLinkNode(template.Node):

    def __init__(self, title):
        self.title = title

    def render(self, context):
        Article = get_article_class()
        
        try:
            v = template.Variable(self.title)
            title = v.resolve(context)
        except template.VariableDoesNotExist:
            title = self.title.strip("'").strip('"')
        
        slug = slugify(title)
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            article = Article.objects.create(slug=slug, title=title)
        
        return article.get_absolute_url()

@register.tag
def article_link(parser, token):
    title = token.split_contents()[1]
    return ArticleLinkNode(title)
