from django.urls import path
from dashboard.views import DashboardHomeView, ProfileView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("profile/", ProfileView.as_view(), name="profile"),
]