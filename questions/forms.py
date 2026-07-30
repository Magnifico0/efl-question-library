from django import forms 
from questions.models import Question,Choice,MatchingPair,Passage
from django.forms import inlineformset_factory
from django.conf import settings

class QuestionForms(forms.ModelForm):
    """
    QuestionForm : organization and created by fileds
    """
    class Meta: 
        model = Question
        fields = ["level","text","image","audio","audio_label",
                  "question_type","section",
                  "correct_answer_text","word_count_instruction", 
                  "is_active","tags"]
        widgets = {
            "level" : forms.Select(attrs={"class" : "form-select",}),
            "text": forms.Textarea(attrs={"class": "form-control","rows": 4,}),
            "image": forms.FileInput(attrs={"class": "form-control",}),
            "audio" : forms.FileInput(attrs={"class":"form-control"}),
            "audio_label": forms.TextInput(attrs={"class":"form-control","placeholder":"Part X"}),
            "question_type": forms.Select(attrs={"class":"form-select",}),
            "section":forms.Select(attrs={"class":"form-select",}),
            "correct_answer_text": forms.TextInput(attrs={"class":"form-control",}),
            "word_count_instruction":forms.TextInput(attrs={"class":"form-control","placeholder":"Örn: En az 150 kelime yazın."}),
            "is_active" : forms.CheckboxInput(attrs={"class":"form-check-input",}),
            "tags": forms.CheckboxSelectMultiple()
        }
    def __init__(self,*args,passage=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.passage = passage
        enabled = settings.ENABLED_SECTIONS
        self.fields["section"].choices = [
            (val,label) for val,label in Question.Section.choices if val in enabled
        ]
        if self.passage is not None:
            self.fields["level"].disabled = True
            self.fields["level"].initial = self.passage.level #değişti dikkat et
            self.fields["section"].disabled = True
            self.fields["section"].initial = self.passage.kind #değişti dikkat et
    def clean(self):
        data = super().clean()
        question_type = data.get("question_type")
        correct_answer_text = data.get("correct_answer_text")
        if question_type == Question.QuestionType.FIB and not correct_answer_text:
            self.add_error(
                "correct_answer_text",
                "Fill in the Blank için doğru cevap girilmesi gerekir."
            )
        return data


class ChoiceForm(forms.ModelForm):
    class Meta: 
        model =  Choice
        fields =  ["text","is_correct"]
        widgets = {
            "text" : forms.TextInput(attrs={"class": "form-control"}),
            "is_correct": forms.CheckboxInput(attrs={"class":"form-check-input"})
        }
ChoiceFormSet = inlineformset_factory(
    parent_model=Question,
    model=Choice,
    form=ChoiceForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True
)

class MatchingPairForm(forms.ModelForm):
    class Meta:
        model = MatchingPair
        fields = ["left_text","right_text"]
        widgets = {
            "left_text": forms.TextInput(attrs={"class": "form-control" }),
            "right_text": forms.TextInput(attrs={"class": "form-control" }),
        }
MatchingPairFormSet= inlineformset_factory(
    parent_model=Question,
    model=MatchingPair,
    form=MatchingPairForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)

class PassageForm(forms.ModelForm):
    class Meta:
        model = Passage
        fields = ["kind", "level", "text", "audio", "audio_label", "image", "image_label"]
        widgets = {
            "kind": forms.Select(attrs={"class": "form-select"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "audio": forms.FileInput(attrs={"class": "form-control"}),
            "audio_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Part 1"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "image_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Image 1"}),
        }

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        if kind == Passage.Kind.READING and not cleaned.get("text"):
            self.add_error("text", "Reading passage için metin girilmesi gerekir.")
        if kind == Passage.Kind.LISTENING and not cleaned.get("audio") and not self.instance.audio:
            self.add_error("audio", "Listening passage için ses dosyası yüklenmesi gerekir.")
        return cleaned