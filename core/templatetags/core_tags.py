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