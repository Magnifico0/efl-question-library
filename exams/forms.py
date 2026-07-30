from django import forms
from questions.models import Question, Tag


class ExamGenerationForm(forms.Form):
    """
    ModelForm değil, çünkü Exam.parameters JSON alanı doğrudan
    form alanlarına 1:1 karşılık gelmiyor — clean() içinde kendi
    JSON yapımızı elle kuruyoruz.
    """
    name = forms.CharField(
        required=False,
        label="Sınav Adı",
        widget=forms.TextInput(attrs={
            "class":"form-control",
            "placeholder":"Boş bırakılırsa tarih otomatik atanır."
        })
    )
    total = forms.IntegerField(
        min_value=1,
        label="Toplam Soru Sayısı",
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_total"}),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label="Etiketler",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for code, label in Question.Level.choices:
            self.fields[f"level_{code}"] = forms.IntegerField(
                min_value=0,
                initial=0,
                required=False,
                label=label,
                widget=forms.NumberInput(attrs={
                    "class": "form-control level-input",
                    "data-level": code,
                }),
            )

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total")

        level_counts = {}
        for code, _ in Question.Level.choices:
            count = cleaned_data.get(f"level_{code}") or 0
            if count > 0:
                level_counts[code] = count

        levels_sum = sum(level_counts.values())
        if total and levels_sum != total:
            raise forms.ValidationError(
                f"Seviyelere göre girilen soru sayıları toplamı ({levels_sum}) "
                f"toplam soru sayısına ({total}) eşit olmalı."
            )

        cleaned_data["level_counts"] = level_counts
        return cleaned_data

    def get_params(self):
        return {
            "name" : self.cleaned_data["name"].strip(),
            "total": self.cleaned_data["total"],
            "levels": self.cleaned_data["level_counts"],
            "tags": [tag.id for tag in self.cleaned_data["tags"]],
        }