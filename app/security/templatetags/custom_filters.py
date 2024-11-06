from django import template

register = template.Library()

@register.filter
def split_at_pipe(value):
    if hasattr(value, 'name'):
        value = value.name
    if isinstance(value, str):
        return value.split('|')[0].strip().capitalize()
    return value
