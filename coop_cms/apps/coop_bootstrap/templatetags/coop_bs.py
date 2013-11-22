from django import template
register = template.Library()

from floppyforms import CheckboxInput

@register.filter(name='is_checkbox')
def is_checkbox(field):
  return field.field.widget.__class__.__name__ == CheckboxInput().__class__.__name__