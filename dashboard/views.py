from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from accounts.mixins import TeacherRequiredMixin
from exams.models import Exam


class DashboardHomeView(TeacherRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exams = Exam.objects.filter(teacher=self.request.user).order_by("-created_at")
        context["recent_exams"] = exams[:5]
        context["total_exam_count"] = exams.count()
        return context


class ProfileView(TeacherRequiredMixin, TemplateView):
    template_name = "dashboard/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context