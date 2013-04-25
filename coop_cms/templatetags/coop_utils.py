# -*- coding: utf-8 -*-

from coop_cms.settings import get_article_class
from coop_cms.utils import get_article
from django import template
register = template.Library()
from django.template.defaultfilters import slugify

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
