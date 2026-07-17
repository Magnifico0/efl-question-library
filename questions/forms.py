from django import forms 
from questions.models import Question,Choice
from django.forms import inlineformset_factory

class QuestionForms(forms.ModelForm):
    """
    QuestionForm : organization and created by fileds
    """
    class Meta: 
        model = Question
        fields = ["level","text","image","audio","audio_label" ,"is_active","tags"]
        widgets = {
            "level" : forms.Select(attrs={"class" : "form-select",}),
            "text": forms.Textarea(attrs={"class": "form-control","rows": 4,}),
            "image": forms.FileInput(attrs={"class": "form-control",}),
            "audio" : forms.FileInput(attrs={"class":"form-control"}),
            "audio": forms.TextInput(attrs={"class":"form-control","placeholder":"Part X"}),
            "is_active" : forms.CheckboxInput(attrs={"class":"form-check-input",}),
            "tags": forms.CheckboxSelectMultiple()
        }

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



