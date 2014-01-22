from django import template
register = template.Library()

from coop_cms.templatetags.coop_utils import is_checkbox as _is_checkbox

#Just for compatibility

@register.filter(name='is_checkbox')
def is_checkbox(field):
  return _is_checkbox(field)