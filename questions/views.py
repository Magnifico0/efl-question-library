from django.shortcuts import render
# Create your views here.

from django.views.generic import ListView, CreateView, UpdateView,DetailView
from django.urls import reverse_lazy,reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect 

from accounts.mixins import ContributorRequiredMixin
from questions.models import Question, Passage
from questions.forms import QuestionForms,ChoiceFormSet,MatchingPairFormSet,PassageForm
from questions.mixins import QuestionSaveMixin

class QuestionListView(ContributorRequiredMixin,ListView):
    model  = Question
    template_name = "questions/question_list.html"
    context_object_name = "questions"


    def get_queryset(self):
        qs = (
            Question.objects.filter(created_by=self.request.user)
            .select_related("created_by","passage")
            .prefetch_related("tags")
            .order_by("-id")
        )
        #ipdb satırı 
        #import ipdb; ipdb.set_trace() 
        #breakpoint()
        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        question_type = self.request.GET.get("question_type")
        if question_type:
            qs = qs.filter(question_type=question_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["questions"]
        standalone,grouped = [],{}
        for q in qs:
            if q.passage_id:
                grouped.setdefault(q.passage,[]).append(q)
            else:
                standalone.append(q)
        context["standalone_questions"] = standalone
        context["grouped_questions"] = grouped
        context["selected_section"] = self.request.GET.get("section", "")
        context["selected_question_type"] = self.request.GET.get("question_type", "")
        context["question_type_choices"] = Question.QuestionType.choices
        return context

class QuestionCreateView(ContributorRequiredMixin,QuestionSaveMixin,CreateView):
    model = Question
    template_name = "questions/question_form.html"
    form_class = QuestionForms #!!!
    success_url = reverse_lazy("questions:list")
    success_message = "Soru başarıyla kaydedildi."

    def get_passage(self):
        passage_id = self.request.GET.get("passage")
        if passage_id: 
            return get_object_or_404(Passage,pk=passage_id,created_by=self.request.user)
        return None 
    def get_from_kwargs(self):
        kwargs = super().get_from_kwargs()
        kwargs["passage"] = self.get_passage()
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["passage"] = self.get_passage()
        return context  

    def get_success_url(self):
        passage = self.get_passage()
        if passage:
            return reverse("questions:passage_detail",kwargs={"pk":passage.pk})
        return reverse("questions:list")

class QuestionUpdateView(ContributorRequiredMixin,QuestionSaveMixin ,UpdateView):
    model = Question
    form_class  = QuestionForms
    template_name  ="questions/question_form.html"
    success_url = reverse_lazy("questions:list")
    success_message  = "Soru güncellendi."

    def get_object(self, queryset = None):
        obj  = get_object_or_404(
            Question,
            pk = self.kwargs["pk"],
            created_by = self.request.user,
        )
        return obj 

    def get_passage(self):
        return self.object.passage

    def get_from_kwargs(self):
        kwargs = super().get_from_kwargs()
        kwargs["passage"] = self.get_passage()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["passage"] = self.get_passage()
        return context

    def get_success_url(self):
        passage  = self.get_passage()
        if passage:
            return reverse("questions:passage_detail",kwargs={"pk":passage.pk})
        return reverse("questions:list")
    
class PassageCreateView(ContributorRequiredMixin, CreateView):
    model = Passage
    form_class = PassageForm
    template_name = "questions/passage_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Paragraf/ses başarıyla kaydedildi.")
        return response

    def get_success_url(self):
        return reverse("questions:passage_detail", kwargs={"pk": self.object.pk})


class PassageDetailView(ContributorRequiredMixin, DetailView):
    model = Passage
    template_name = "questions/passage_detail.html"
    context_object_name = "passage"

    def get_queryset(self):
        return Passage.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_questions"] = (
            self.object.questions.all().prefetch_related("tags").order_by("id")
        )
        return context