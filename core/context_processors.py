def user_role_context(request):
    """
    to use {role} in templates
    """
    if request.user.is_authenticated:
        return {'role': request.user.role}
    return {'role' : None}
