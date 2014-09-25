# -*- coding: utf-8 -*-

from coop_cms.settings import get_article_class
from coop_cms.shortcuts import get_article
from django import template
register = template.Library()
from django.utils.text import slugify
from coop_cms.utils import dehtml as do_dehtml
from bs4 import BeautifulSoup
import unicodedata
from django.conf import settings
from floppyforms import CheckboxInput
from coop_cms.models import ArticleCategory, Image
import os.path

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
                request = context.get('request', None)
                lang = "en"
                if request:
                    lang = request.LANGUAGE_CODE
                elif hasattr(settings, 'LANGUAGES'):
                    lang = settings.LANGUAGES[0][0]
                elif hasattr(settings, 'LANGUAGE_CODE'):
                    lang = settings.LANGUAGE_CODE[:2]
                article = get_article(slug, current_lang=lang)
        except Article.DoesNotExist:
            try:
                article = get_article(slug, all_langs=True)
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
    

@register.filter(name='is_checkbox')
def is_checkbox(field):
    field = getattr(field, 'field', field) # get the field attribute of the field or the field itself
    return field.widget.__class__.__name__ == CheckboxInput().__class__.__name__
    
@register.filter
def index(seq, index):
    try:
        return seq[index]
    except IndexError:
        return None

################################################################################
class CoopCategoryNode(template.Node):

    def __init__(self, cat_slug, var_name):
        cat = cat_slug.strip("'").strip('"')
        self.cat_var, self.cat = None, None
        if cat_slug == cat:
            self.cat_var = template.Variable(cat)
        else:
            self.cat = cat
        self.var_name = var_name

    def render(self, context):
        if self.cat_var:
            self.cat = self.cat_var.resolve(context)
        try:
            slug = slugify(self.cat)
            self.category = ArticleCategory.objects.get(slug=slug)
        except ArticleCategory.DoesNotExist:
            self.category = ArticleCategory.objects.create(name=self.cat)
        context.dicts[0][self.var_name] = self.category
        return ""

@register.tag
def coop_category(parser, token):
    #Newsletter friendly CSS
    args = token.split_contents()
    cat_slug = args[1]
    var_name = args[2]
    return CoopCategoryNode(cat_slug, var_name)


@register.filter
def basename(fullname):
    return os.path.basename(fullname)

@register.filter
def get_parts(list_of_objs, number_of_parts):
    nb_objs = len(list_of_objs)
    nb_by_part, extra_nb = nb_objs/number_of_parts, nb_objs % number_of_parts
    parts = []
    stop_index = 0
    for which_part in range(number_of_parts):
        start_index = 0 if (stop_index==0) else (stop_index)
        stop_index = start_index + nb_by_part + (1 if (which_part<extra_nb) else 0)
        parts.append(list_of_objs[start_index:stop_index])
    return parts

@register.filter
def get_part(list_of_objs, partionning):
    which_part, number_of_parts = [int(x) for x in partionning.split("/")]
    parts = get_parts(list_of_objs, number_of_parts)
    return parts[which_part-1]
    

################################################################################
class ImageListNode(template.Node):

    def __init__(self, filter_name, var_name):
        stripped_filter_name = filter_name.strip("'").strip('"')
        self.filter_var, self.filter_value = None, None
        if stripped_filter_name == filter_name:
            self.filter_var = template.Variable(filter_name)
        else:
            self.filter_value = stripped_filter_name
        self.var_name = var_name

    def render(self, context):
        if self.filter_var:
            self.filter_value = self.filter_var.resolve(context)
        images = Image.objects.filter(filters__name=self.filter_value).order_by("ordering", "-created")
        context.dicts[1][self.var_name] = images
        return ""

@register.tag
def coop_image_list(parser, token):
    args = token.split_contents()
    try:
        filter_name = args[1]
        as_name = args[2]
        var_name = args[3]
    except IndexError:
        raise Exception(u"coop_image_list: usage --> {% coop_image_list 'filter_name' as var_name %}")
    return ImageListNode(filter_name, var_name)
