# -*- coding: utf-8 -*-

from django import template
register = template.Library()
from djaloha.templatetags.djaloha_utils import DjalohaEditNode, DjalohaMultipleEditNode
from coop_cms.models import PieceOfHtml, BaseArticle, Fragment, FragmentType, FragmentFilter
from django.utils.translation import ugettext_lazy as _
from django.core.context_processors import csrf
from django.utils.safestring import mark_safe
from coop_cms.widgets import ImageEdit
from coop_cms.settings import get_article_class
from django.template.loader import find_template, TemplateDoesNotExist
import logging
logger = logging.getLogger("coop_cms")

################################################################################
class PieceOfHtmlEditNode(DjalohaEditNode):
    
    def render(self, context):
        if context.get('form', None) or context.get('formset', None):
            context.dicts[0]['djaloha_edit'] = True
        #context.dicts[0]['can_edit_template'] = True
        return super(PieceOfHtmlEditNode, self).render(context)

@register.tag
def coop_piece_of_html(parser, token):
    args = token.split_contents()
    div_id = args[1]
    read_only = False
    if len(args)>2:
        read_only = (args[2]=="read-only")
    return PieceOfHtmlEditNode(PieceOfHtml, {'div_id': div_id}, 'content', read_only)

################################################################################

class FragmentEditNode(DjalohaMultipleEditNode):
    
    def _get_objects(self, lookup):
        self.fragment_type, _x = FragmentType.objects.get_or_create(name=lookup['name'])
        qs = Fragment.objects.filter(type=self.fragment_type)
        if lookup.has_key('extra_id'):
            self.fragment_filter, _x = FragmentFilter.objects.get_or_create(extra_id=lookup['extra_id'])
            qs = qs.filter(filter=self.fragment_filter)
        return qs
    
    def _get_object_lookup(self, obj):
        return {"id": obj.id}

    def __init__(self, lookup, kwargs=None):
        super(FragmentEditNode, self).__init__(Fragment, lookup, 'content')
        self.fragment_filter = None
        self.kwargs = kwargs or {}
    
    def _pre_object_render(self, obj):
        return u'<div class="coop-fragment {0}" rel="{1}">'.format(obj.css_class, obj.id)
    
    def _post_object_render(self, obj):
        return u'</div>'
    
    def _object_render(self, idx, obj, context):
        value = getattr(obj, self._field_name)
        template_name = self.kwargs.get('template_name', '')
        if template_name:
            template_name = self._resolve_arg(template_name, context)
            t, _o = find_template(template_name)
            object_content = t.render(template.Context({
                'index': idx,
                'fragment': self._render_value(context, self._get_object_lookup(obj), value),
                'form': self._edit_mode #if_cms_edition --> active
            }))
        else:
            object_content = self._pre_object_render(obj)
            object_content += self._render_value(context, self._get_object_lookup(obj), value)
            object_content += self._post_object_render(obj)
        return object_content
    
    def render(self, context):
        self._edit_mode = False
        if context.get('form', None) or context.get('formset', None):
            context.dicts[0]['djaloha_edit'] = True
            self._edit_mode = True
        #context.dicts[0]['can_edit_template'] = True
        html = super(FragmentEditNode, self).render(context)
        filter_id = self.fragment_filter.id if self.fragment_filter else ""
        pre_html = u'<div style="display: none" class="coop-fragment-type" rel="{0}" data-filter="{2}">{1}</div>'.format(
            self.fragment_type.id, self.fragment_type.name, filter_id)
        return pre_html+html

@register.tag
def coop_fragments(parser, token):
    args = token.split_contents()
    lookup = {'name': args[1]}
    if len(args) > 2:
        args2 = args[2]
        if args2.find("=")<0:
            lookup["extra_id"] = args2
    kwargs = {}
    for arg in args[2:]:
        if arg.find("=")>0:
            k, v = arg.split('=')
            kwargs[k] = v
    return FragmentEditNode(lookup, kwargs)

################################################################################
class ArticleSummaryEditNode(DjalohaEditNode):
    def render(self, context):
        if context.get('form', None):
            context.dicts[0]['djaloha_edit'] = True
        #context.dicts[0]['can_edit_template'] = True
        return super(ArticleSummaryEditNode, self).render(context)

@register.tag
def article_summary_edit(parser, token):
    Article = get_article_class()
    id = token.split_contents()[1]
    return ArticleSummaryEditNode(Article, {'id': id}, 'summary')

################################################################################
class ArticleTitleNode(template.Node):

    def render(self, context):
        is_edition_mode = context.get('form', None)!=None
        article = context.get('article')
        return u"{0}".format(
            article.title,
            _(u" [EDITION]") if is_edition_mode else u"",
            _(u" [DRAFT]") if article.publication == BaseArticle.PUBLISHED else u"",
        )

@register.tag
def article_title(parser, token):
    return ArticleTitleNode()

################################################################################


class CmsFormMediaNode(template.Node):

    def render(self, context):
        form = context.get('form', None)
        formset = context.get('formset', None)
        if form or formset:
            t = template.Template("{{form.media}}")
            html = t.render(template.Context({'form': form or formset}))
            #django 1.5 fix : " are escaped as &quot; and cause script tag 
            #for aloha to be broken
            return html.replace("&quot;", '"') 
        else:
            return ""

@register.tag
def cms_form_media(parser, token):
    return CmsFormMediaNode()


################################################################################

def _extract_if_node_args(parser, token):
    nodelist_true = parser.parse(('else', 'endif'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endif',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return nodelist_true, nodelist_false

class IfCmsEditionNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def __iter__(self):
        for node in self.nodelist_true:
            yield node
        for node in self.nodelist_false:
            yield node

    def _check_condition(self, context):
        return context.get('form', None) or context.get('formset', None) 

    def render(self, context):
        if self._check_condition(context):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def if_cms_edition(parser, token):
    nodelist_true, nodelist_false = _extract_if_node_args(parser, token)
    return IfCmsEditionNode(nodelist_true, nodelist_false)

class IfNotCmsEditionNode(IfCmsEditionNode):
    def _check_condition(self, context):
        return not super(IfNotCmsEditionNode, self)._check_condition(context)
        
@register.tag
def if_not_cms_edition(parser, token):
    nodelist_true, nodelist_false = _extract_if_node_args(parser, token)
    return IfNotCmsEditionNode(nodelist_true, nodelist_false)


################################################################################


CMS_FORM_TEMPLATE = """
<form id="cms_form" enctype="multipart/form-data"  method="POST" action="{{post_url}}">{% csrf_token %}
    {% include "coop_cms/_form_error.html" with errs=form.non_field_errors %}
    {{inner}} <input type="submit" style="display: none"> </form>
"""

class SafeWrapper:

    def __init__(self, wrapped, logo_size=None, logo_crop=None):
        self._wrapped = wrapped
        self._logo_size = logo_size
        self._logo_crop = logo_crop

    def __getattr__(self, field):
        value = getattr(self._wrapped, field)
        
        if hasattr(value, 'pk'):
            return value
        elif field=='logo':
            src = getattr(self._wrapped, 'logo_thumbnail')(False, self._logo_size, self._logo_crop)
            if src:
                try:
                    t, _o = find_template("coop_cms/widgets/_img_logo.html")
                    value = t.render(template.Context({'url': src.url}))
                except TemplateDoesNotExist:
                    value = u'<img class="logo" src="{0}" />'.format(src.url)
                except Exception, msg:
                        logger.exception("coop_edition:SafeWrapper")
            else:
                value = u''
        elif callable(value):
            return value()
        return mark_safe(value)

class FormWrapper:

    def __init__(self, form, obj, logo_size=None, logo_crop=None):
        self._form = form
        self._obj = obj
        if logo_size:
            self._form.set_logo_size(logo_size, logo_crop)

    def __getitem__(self, field, logo_size=None):
        if field in self._form.fields.keys():
            t = template.Template("""
                    {%% with form.%s.errors as errs %%}{%% include "coop_cms/_form_error.html" %%}{%% endwith %%}{{form.%s}}
                """ % (field, field))
            return t.render(template.Context({'form': self._form}))
        else:
            return getattr(self._obj, field)

class CmsEditNode(template.Node):

    def __init__(self, nodelist_content, var_name, logo_size=None, logo_crop=None):
        self.var_name = var_name
        self.nodelist_content = nodelist_content
        self._logo_size = logo_size.strip("'").strip('"') if logo_size else None
        self._logo_crop = logo_crop.strip("'").strip('"') if logo_crop else None
        self._render_logo_size = self._logo_size and (self._logo_size!=logo_size)
        self._render_logo_crop = self._logo_crop and (self._logo_crop!=logo_crop)

    def __iter__(self):
        for node in self.nodelist_content:
            yield node

    def render(self, context):
        request = context.get('request')
        
        form = context.get('form', None)
        obj = context.get(self.var_name, None) if self.var_name else None
        
        if self._render_logo_size:
            self._logo_size = context.get(self._logo_size, None)
            
        if self._render_logo_crop:
            self._logo_crop = context.get(self._logo_crop, None)
        
        formset = context.get('formset', None)
        objects = context.get('objects', None)

        #the context used for rendering the templatetag content
        inner_context = {}
        for x in context.dicts:
            inner_context.update(x)

        #the context used for rendering the whole page
        self.post_url = obj.get_edit_url() if obj else context.get('coop_cms_edit_url')
        outer_context = {'post_url': self.post_url}

        if self.var_name:
            inner_context[self.var_name] = obj
        if formset:
            inner_context['formset'] = formset
        if objects:
            inner_context['objects'] = objects

        safe_context = inner_context.copy()
        #inner_context[self.var_name] = obj
        inner_value = u""

        if form or formset:
            t = template.Template(CMS_FORM_TEMPLATE)
            if form:
                safe_context[self.var_name] = FormWrapper(
                    form, obj, logo_size=self._logo_size, logo_crop=self._logo_crop)
            else:
                safe_context['objects'] = [
                    FormWrapper(f, o, logo_size=self._logo_size, logo_crop=self._logo_crop)
                    for (f, o) in zip(formset, objects)
                ]
            outer_context.update(csrf(request))
            #outer_context['inner'] = self.nodelist_content.render(template.Context(inner_context))
        else:
            t = template.Template("{{inner|safe}}")
            if obj:
                safe_context[self.var_name] = SafeWrapper(
                    obj, logo_size=self._logo_size, logo_crop=self._logo_crop)
            else:
                safe_context['objects'] = [
                    SafeWrapper(o, logo_size=self._logo_size, logo_crop=self._logo_crop) for o in objects
                ]
                
        managed_node_types = [
            template.TextNode, template.defaulttags.IfNode, template.defaulttags.ForNode,
            IfCmsEditionNode, IfNotCmsEditionNode,
        ]
                
        for node in self.nodelist_content:
            #node.is_safe = True
            if any([isinstance(node, node_type) for  node_type in managed_node_types]):
                c = node.render(template.Context(safe_context))
            elif isinstance(node, template.loader_tags.BlockNode):
                sf = template.Context(safe_context)
                sf.render_context['block_context'] = context.render_context.get('block_context', None)
                c = node.render(sf)
            elif isinstance(node, template.VariableNode):
                if node.filter_expression.filters:
                    c = node.render(context)
                else:
                    c = node.render(template.Context(safe_context))   
            else:
                c = node.render(template.Context(inner_context))
            inner_value += c
        outer_context['inner'] = mark_safe(inner_value) if (form or formset) else inner_value
        return t.render(template.Context(outer_context))

@register.tag
def cms_edit(parser, token):
    args = token.split_contents()[1:]
    data = {}
    var_name = args[0] if len(args) else ''
    for arg in args[1:]:
        k, v = arg.split('=')
        data[k] = v
    nodelist = parser.parse(('end_cms_edit',))
    token = parser.next_token()
    return CmsEditNode(nodelist, var_name, **data)

################################################################################

class CmsNoSpace(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        html = self.nodelist.render(context).strip()
        return ' '.join(html.split())

@register.tag
def cms_nospace(parser, token):
    nodelist = parser.parse(('end_cms_nospace',))
    parser.delete_first_token()
    return CmsNoSpace(nodelist)
