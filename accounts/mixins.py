from django.shortcuts import redirect
class TeacherRequiredMixin:
    """
    check for is the user teacher
    """
    def dispatch(self,request,*args,**kwargs):
        if not request.user.is_authenticated:
            return redirect("/login/")
        if request.user.role != "teacher":
            return redirect("/login/")
        return super().dispatch(request,*args,**kwargs)
    
class OrgAdminRequiredMixin:
    """
    check for is the user organization admin 
    """
    def dispatch(self,request,*args,**kwargs):
        if not request.user.is_authenticated: 
            return redirect("/login/")
        if request.user.role !="org_admin":
            return redirect("/login/")
        return super().dispatch(request,*args,**kwargs)
    
class AdminRequiredMixin:
    """
    check for is the user admin
    """
    def dispatch(self,request,*args,**kwargs):
        if not request.user.is_authenticated:
            return redirect("/login/")
        if request.user.role !="admin":
            return redirect("/login/")
        return super().dispatch(request,*args,**kwargs)
    

class ContributorRequiredMixin: 
    """
    check for is the user contributor
    """
    def dispatch(self,request,*args,**kwargs):
        if not request.user.is_authenticated: 
            return redirect("/login/")
        if request.user.role !="contributor":
            return redirect("/login/")
        return super().dispatch(request,*args,**kwargs)