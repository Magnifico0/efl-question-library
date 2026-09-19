from django.views.generic import View, DetailView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from accounts.mixins import TeacherRequiredMixin
from questions.models import Level
from exams.models import Exam
from exams.forms import ExamGenerationForm, PassageSlotFormSet
from exams.services import ExamGeneratorService, ExamGenerationError
import random


def _shuffle_choices_for_exam(exam, questions):
    for question in questions:
        seed = exam.pk * 10000042 + question.pk
        rng = random.Random(seed)
        shuffled = list(question.choices.all())
        rng.shuffle(shuffled)
        question.shuffled_choices = shuffled


def _prepare_matching_for_exam(exam, questions):
    """Her matching sorusu için: sol sütun sabit sıralı, sağ sütun karışık."""
    for question in questions:
        pairs = list(question.matching_pairs.all())
        if pairs:
            seed = exam.pk * 10000043 + question.pk
            rng = random.Random(seed)
            right_texts = [p.right_text for p in pairs]
            shuffled_right = right_texts[:]
            rng.shuffle(shuffled_right)
            question.matching_display = list(zip(pairs, shuffled_right))
        else:
            question.matching_display = None


def _build_render_blocks(questions):
    """
    `questions` zaten doğru sırada (through model + Meta.ordering sayesinde),
    ve passage'a bağlı sorular her zaman ardışık geliyor (Stage 11 garantisi).
    """
    blocks = []
    current_group = None
    number = 0

    for question in questions:
        number += 1
        question.exam_number = number

        if question.passage_id is not None:
            if current_group is not None and current_group["passage_id"] == question.passage_id:
                current_group["questions"].append(question)
            else:
                current_group = {
                    "type": "passage_group",
                    "passage": question.passage,
                    "passage_id": question.passage_id,
                    "questions": [question],
                }
                blocks.append(current_group)
        else:
            current_group = None
            blocks.append({"type": "standalone", "question": question})

    return blocks


class ExamCreateView(TeacherRequiredMixin, View):
    template_name = "exams/create.html"

    def _build_context(self, form, reading_formset, listening_formset):
        return {
            "form": form,
            "reading_formset": reading_formset,
            "listening_formset": listening_formset,
            "level_choices": [code for code, _ in Level.choices],
        }

    def get(self, request):
        return render(request, self.template_name, self._build_context(
            ExamGenerationForm(),
            PassageSlotFormSet(prefix="reading"),
            PassageSlotFormSet(prefix="listening"),
        ))

    def post(self, request):
        form = ExamGenerationForm(request.POST)
        reading_formset = PassageSlotFormSet(request.POST, prefix="reading")
        listening_formset = PassageSlotFormSet(request.POST, prefix="listening")

        all_valid = form.is_valid() & reading_formset.is_valid() & listening_formset.is_valid()

        if all_valid:
            reading_slots = ExamGenerationForm.slots_from_formset(reading_formset)
            listening_slots = ExamGenerationForm.slots_from_formset(listening_formset)

            form.validate_against_slots(reading_slots, listening_slots)

            if not form.errors:
                params = form.get_params(reading_slots, listening_slots)
                try:
                    service = ExamGeneratorService(teacher=request.user, params=params)
                    exam = service.generate()
                    messages.success(request, "Sınav başarıyla oluşturuldu.")
                    return redirect("exams:preview", pk=exam.pk)
                except ExamGenerationError as e:
                    form.add_error(None, str(e))

        return render(request, self.template_name,
                      self._build_context(form, reading_formset, listening_formset))


class ExamPreviewView(TeacherRequiredMixin, DetailView):
    model = Exam
    template_name = "exams/preview.html"
    context_object_name = "exam"

    def get_object(self, queryset=None):
        return get_object_or_404(Exam, pk=self.kwargs["pk"], teacher=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = list(self.object.questions.all().select_related("passage")
                         .prefetch_related("choices", "matching_pairs"))
        _shuffle_choices_for_exam(self.object, questions)
        _prepare_matching_for_exam(self.object, questions)
        context["questions"] = questions
        context["render_blocks"] = _build_render_blocks(questions)
        return context


class ExamDownloadView(TeacherRequiredMixin, View):
    def get(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
        questions = list(exam.questions.all().select_related("passage")
                         .prefetch_related("choices", "matching_pairs"))

        _shuffle_choices_for_exam(exam, questions)
        _prepare_matching_for_exam(exam, questions)
        render_blocks = _build_render_blocks(questions)

        html_string = render_to_string("exams/pdf.html", {
            "exam": exam,
            "questions": questions,
            "render_blocks": render_blocks,
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