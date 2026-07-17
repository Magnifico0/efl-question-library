from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm


def login_view(request):
    # zaten giriş yapmışsa yönlendir
    if request.user.is_authenticated:
        return role_redirect(request.user)
    
    form = LoginForm()
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return role_redirect(user)
            else:
                form.add_error(None, "Kullanıcı adı veya şifre hatalı.")
    
    return render(request, "accounts/login.html", {"form": form})


def role_redirect(user):
    if user.role == "admin":
        return redirect("/admin/")
    elif user.role == "org_admin":
        return redirect("/org/")
    elif user.role == "contributor":
        return redirect("/questions/")
    else:
        return redirect("/dashboard/")


def logout_view(request):
    logout(request)
    return redirect("/login/")