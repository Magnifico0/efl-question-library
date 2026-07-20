from django import template 

register  =template.Library()

@register.simple_tag
def active_nav(request,url):
    """
    for bootstrap navbar active class
    """
    if request.path ==url:
        return "active"
    return ""

@register.filter
def to_letter(value):
    """1 -> A, 2 -> B, 3 -> C ..."""
    try:
        return chr(64 + int(value))
    except (ValueError, TypeError):
        return value