# -*- coding: utf-8 -*-
"""utils"""

from django.template.loader import get_template


def get_model_name(model_class):
    """return model name"""
    meta_class = getattr(model_class, '_meta')
    return getattr(meta_class, 'module_name', '') or getattr(meta_class, 'model_name')


def get_model_label(model_class):
    """return model name"""
    meta_class = getattr(model_class, '_meta')
    return getattr(meta_class, 'verbose_name')


def get_model_app(model_class):
    """return app name for this model"""
    meta_class = getattr(model_class, '_meta')
    return getattr(meta_class, 'app_label')


def get_text_from_template(template_name, extra_context=None):
    """
    load a template and render it as text
    :parameter template_name: the path to a template
    :parameter extra_context: some context for rendering
    :return text
    """
    context = extra_context or {}
    template = get_template(template_name)
    return template.render(context)
