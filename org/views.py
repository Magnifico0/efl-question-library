from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q

from accounts.mixins import OrgAdminRequiredMixin
from accounts.models import User
from questions.models import Question
from exams.models import Exam
from org.forms import TeacherCreateForm


class OrgDashboardView(OrgAdminRequiredMixin, TemplateView):
    template_name = "org/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization

        context["teacher_count"] = User.objects.filter(
            organization=org, role="teacher"
        ).count()
        context["question_count"] = Question.objects.filter(
            Q(organization=None) | Q(organization=org)
        ).count()
        context["exam_count"] = Exam.objects.filter(organization=org).count()
        return context


class TeacherListView(OrgAdminRequiredMixin, ListView):
    model = User
    template_name = "org/teacher_list.html"
    context_object_name = "teachers"

    def get_queryset(self):
        return User.objects.filter(
            organization=self.request.user.organization,
            role="teacher",
        ).order_by("first_name", "last_name")


class TeacherCreateView(OrgAdminRequiredMixin, CreateView):
    model = User
    form_class = TeacherCreateForm
    template_name = "org/teacher_form.html"
    success_url = reverse_lazy("org:teacher_list")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = "teacher"
        user.organization = self.request.user.organization
        user.save()
        messages.success(self.request, "Öğretmen başarıyla eklendi.")
        return redirect(self.success_url)


class TeacherDetailView(OrgAdminRequiredMixin, DetailView):
    model = User
    template_name = "org/teacher_detail.html"
    context_object_name = "teacher"

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            pk=self.kwargs["pk"],
            organization=self.request.user.organization,
            role="teacher",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exams"] = Exam.objects.filter(
            teacher=self.object
        ).order_by("-created_at")
        return context


class OrgQuestionListView(OrgAdminRequiredMixin, ListView):
    model = Question
    template_name = "org/question_list.html"
    context_object_name = "questions"

    def get_queryset(self):
        org = self.request.user.organization
        return (
            Question.objects.filter(Q(organization=None) | Q(organization=org))
            .select_related("created_by")
            .prefetch_related("tags")
            .order_by("-id")
        )


class OrgExamListView(OrgAdminRequiredMixin, ListView):
    model = Exam
    template_name = "org/exam_list.html"
    context_object_name = "exams"

    def get_queryset(self):
        return Exam.objects.filter(
            organization=self.request.user.organization
        ).order_by("-created_at")