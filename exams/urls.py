from django.urls import path
from exams.views import ExamCreateView, ExamPreviewView, ExamDownloadView, ExamHistoryView

app_name = "exams"

urlpatterns = [
    path("create/", ExamCreateView.as_view(), name="create"),
    path("<int:pk>/preview/", ExamPreviewView.as_view(), name="preview"),
    path("<int:pk>/download/", ExamDownloadView.as_view(), name="download"),
    path("history/", ExamHistoryView.as_view(), name="history"),
]