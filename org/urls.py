from django.urls import path
from org.views import (
    OrgDashboardView,
    TeacherListView,
    TeacherCreateView,
    TeacherDetailView,
    OrgQuestionListView,
    OrgExamListView,
)

app_name = "org"

urlpatterns = [
    path("", OrgDashboardView.as_view(), name="dashboard"),
    path("teachers/", TeacherListView.as_view(), name="teacher_list"),
    path("teachers/add/", TeacherCreateView.as_view(), name="teacher_create"),
    path("teachers/<int:pk>/", TeacherDetailView.as_view(), name="teacher_detail"),
    path("questions/", OrgQuestionListView.as_view(), name="question_list"),
    path("exams/", OrgExamListView.as_view(), name="exam_list"),
]