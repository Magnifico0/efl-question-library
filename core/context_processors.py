from django.conf import settings
from questions.models import Question
def user_role_context(request):
    """
    to use {role} in templates
    """
    if request.user.is_authenticated:
        return {'role': request.user.role}
    return {'role' : None}

def enabled_sections(request):
    """
    for section filter dropdown
    """
    enabled = settings.ENABLED_SECTIONS
    return {
        "enabled_sections":enabled,
        "enabled_sections_choices":[
            (val,label) for val,label in Question.Section.choices if val in enabled
        ],}
