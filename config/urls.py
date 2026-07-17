"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden

def dashboard_placeholder(request):
    if not request.user.is_authenticated or request.user.role != "teacher":
        return HttpResponseForbidden("Erişim engellendi")
    return HttpResponse("Dashboard - yakında")


def org_placeholder(request):
    if not request.user.is_authenticated or request.user.role != "org_admin":
        return HttpResponseForbidden("Erişim engellendi")
    return HttpResponse("Org Admin - yakında")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("accounts.urls")),
    path("dashboard/", dashboard_placeholder), #temporary 
    path("org/", org_placeholder), #temporary 
    path("questions/",include("questions.urls"), name="questions"),
]
