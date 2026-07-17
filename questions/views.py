from django.shortcuts import render
# Create your views here.

from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect 

from accounts.mixins import ContributorRequiredMixin
from questions.models import Question
from questions.forms import QuestionForms,ChoiceFormSet

class QuestionListView(ContributorRequiredMixin,ListView):
    model  = Question
    template_name = "questions/question_list.html"
    context_object_name = "questions"

    def get_queryset(self):
        #select_related -> takes with JOIN not SQL query for each line
        return (
            Question.objects.filter(created_by=self.request.user).select_related("created_by")
            .prefetch_related("tags") #for M2M use prefetch_related not select_related 
            .order_by("-id")
        )
    
class QuestionCreateView(ContributorRequiredMixin,CreateView):
    model = Question
    template_name = "questions/question_form.html"
    form_class = QuestionForms #!!!
    success_url = reverse_lazy("questions:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["choice_formset"]  = ChoiceFormSet(self.request.POST)
        else: 
            context["choice_formset"] = ChoiceFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]

        if choice_formset.is_valid():
            question = form.save(commit=False)
            question.created_by = self.request.user

            has_choices = any(
                cf.cleaned_data.get("text") and not cf.cleaned_data.get("DELETE")
                for cf in choice_formset
                if cf.cleaned_data
            )
            question.is_active = has_choices
            question.save()
            form.save_m2m()
            choice_formset.instance = question
            choice_formset.save()
            messages.success(self.request,"Soru başarıyla kaydedildi.")
            return redirect(self.success_url)
        else: 
            return self.render_to_response(
                self.get_context_data(form=form)
            )

class QuestionUpdateView(ContributorRequiredMixin, UpdateView):
    model = Question
    form_class  = QuestionForms
    template_name  ="questions/question_form.html"
    success_url = reverse_lazy("questions:list")

    def get_object(self, queryset = None):
        obj  = get_object_or_404(
            Question,
            pk = self.kwargs["pk"],
            created_by = self.request.user,
        )
        return obj 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["choice_formset"] =  ChoiceFormSet(
                self.request.POST,
                instance=self.object,
            )
        else: 
            context["choice_formset"] = ChoiceFormSet(instance=self.object)
        return context 
    def form_valid(self,form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]

        if choice_formset.is_valid():
            question = form.save(commit=False)
            question.created_by = self.request.user
            
            has_choices = any(
                cf.cleaned_data.get("text") and not cf.cleaned_data.get("DELETE")
                for cf in choice_formset
                if cf.cleaned_data
            )

            question.is_active  =has_choices
            question.save()
            form.save_m2m()
            choice_formset.instance = question
            choice_formset.save()
            messages.success(self.request, "Soru güncellendi. ")
            return redirect(self.success_url)
        else: 
            return self.render_to_response(
                self.get_context_data(form=form)
            )
        
