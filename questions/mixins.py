from django.contrib import messages
from django.shortcuts import redirect
from questions.models import Question
from questions.forms import ChoiceFormSet, MatchingPairFormSet


class QuestionSaveMixin:
    """
    QuestionCreateView ve QuestionUpdateView ortak form_valid() mantığı
    question_type'a göre 4 dal: fib, matching, open_ended, mc/tf
    """
    success_message = "Soru başarıyla kaydedildi."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = getattr(self, "object", None)
        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(
                self.request.POST,
                instance=instance,
                
                prefix="choices"
            )
            context["matching_formset"] = MatchingPairFormSet(
                self.request.POST,
                instance=instance,
                prefix="matching"
            )
        else:
            context["choice_formset"] = ChoiceFormSet(
                instance=instance,
                prefix="choices"
            )
            context["matching_formset"] = MatchingPairFormSet(
                instance=instance,
                prefix="matching"
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        choice_formset = context["choice_formset"]
        matching_formset = context["matching_formset"]
        question_type = form.cleaned_data["question_type"]

        formset = {
            Question.QuestionType.MC: choice_formset,
            Question.QuestionType.TF: choice_formset,
            Question.QuestionType.MATCHING: matching_formset,
        }.get(question_type)  # fib ve open_ended için None döner

        if formset is not None and not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        question = form.save(commit=False)
        question.created_by = self.request.user
        passage = self.get_passage()
        if passage is not None:
            question.passage = passage
            question.level = passage.level 
            question.section = passage.kind

        question.is_active = self._compute_is_active(question_type, question, formset)
        question.save()
        form.save_m2m()

        if formset is not None:
            formset.instance = question
            formset.save()

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())

    def _compute_is_active(self, question_type, question, formset):
        if question_type == Question.QuestionType.FIB:
            return bool(question.correct_answer_text)
        if question_type == Question.QuestionType.OPEN_ENDED:
            return bool(question.text)
        if question_type == Question.QuestionType.MATCHING:
            return any(
                f.cleaned_data.get("left_text") and f.cleaned_data.get("right_text") and not f.cleaned_data.get("DELETE")
                for f in formset
                if f.cleaned_data
            )
        # mc, tf
        return any(
            f.cleaned_data.get("text") and not f.cleaned_data.get("DELETE")
            for f in formset
            if f.cleaned_data
        )