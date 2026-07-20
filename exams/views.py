from django.views.generic import View, DetailView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from accounts.mixins import TeacherRequiredMixin
from exams.models import Exam
from exams.forms import ExamGenerationForm
from exams.services import ExamGeneratorService, ExamGenerationError


class ExamCreateView(TeacherRequiredMixin, View):
    template_name = "exams/create.html"

    def get(self, request):
        form = ExamGenerationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ExamGenerationForm(request.POST)
        if form.is_valid():
            params = form.get_params()
            try:
                service = ExamGeneratorService(teacher=request.user, params=params)
                exam = service.generate()
                messages.success(request, "Sınav başarıyla oluşturuldu.")
                return redirect("exams:preview", pk=exam.pk)
            except ExamGenerationError as e:
                form.add_error(None, str(e))
        return render(request, self.template_name, {"form": form})


class ExamPreviewView(TeacherRequiredMixin, DetailView):
    model = Exam
    template_name = "exams/preview.html"
    context_object_name = "exam"

    def get_object(self, queryset=None):
        return get_object_or_404(Exam, pk=self.kwargs["pk"], teacher=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.questions.all().prefetch_related("choices")
        return context


class ExamDownloadView(TeacherRequiredMixin, View):
    def get(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
        questions = exam.questions.all().prefetch_related("choices")

        html_string = render_to_string("exams/pdf.html", {
            "exam": exam,
            "questions": questions,
        })

        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="exam_{exam.pk}.pdf"'
        return response


class ExamHistoryView(TeacherRequiredMixin, ListView):
    model = Exam
    template_name = "exams/history.html"
    context_object_name = "exams"

    def get_queryset(self):
        return Exam.objects.filter(teacher=self.request.user).order_by("-created_at")