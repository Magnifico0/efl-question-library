from django import forms
from questions.models import Question, Tag, Level


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
    #reading params 
    reading_passage_count = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label="Paragraf Sayısı",
        widget=forms.NumberInput(attrs={
            "class": "form-control passage-input"
        }), 
    )
    
    reading_questions_per_passage = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label="Paragraf Başına Soru Sayısı (Reading)",
        widget=forms.NumberInput(attrs={"class": "form-control passage-input"}),
    )

    reading_questions_total = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label="Toplam Paragraf Soru Sayısı (Reading)",
        widget=forms.NumberInput(attrs={"class":"form-control passage-input"})
    )
    #listening params 
    listening_passage_count = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label="Listening Passage Sayısı",
        widget=forms.NumberInput(attrs={"class": "form-control passage-input"}),
    )
    listening_questions_per_passage = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label="Paragraf Başına Soru Sayısı (Listening)",
        widget=forms.NumberInput(attrs={"class": "form-control passage-input"}),
    )
    listening_questions_total = forms.IntegerField(
        min_value=0, initial=0, required=False,
        label="Listening Parçalarından Toplam Soru Sayısı",
        widget=forms.NumberInput(attrs={"class":"form-control passage-input"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for code, label in Level.choices:
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

    def _validate_passage_section(self,cleaned_data,section_label,prefix):
        """
        reading ve listening için kontrol şeması, yardımcı function
        """
        count = cleaned_data.get(f"{prefix}_passage_count") or 0
        per_passage = cleaned_data.get(f"{prefix}_questions_per_passage") or 0 
        total = cleaned_data.get(f"{prefix}_questions_total") or 0
        if count <=0:
            return 0 
        if per_passage >0 and total>0:
            raise forms.ValidationError(
                f"{section_label} için passage başına soru sayısı ile toplam soru "
                f"sayısının aynı anda girmeyin - sadece birini kullanın."
            )
        if per_passage <=0 and total <=0:
            raise forms.ValidationError(
                f"{section_label} parça sayısı girdiyseniz, passage başına soru "
                f"sayısının veya toplam soru sayısından birini girmelisiniz."
            )
        return (count * per_passage) if per_passage > 0 else total 
    
    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total")

        level_counts = {}
        for code, _ in Level.choices:
            count = cleaned_data.get(f"level_{code}") or 0
            if count > 0:
                level_counts[code] = count

        levels_sum = sum(level_counts.values())

        reading_questions_total = self._validate_passage_section(
            cleaned_data,"Reading","reading"
        )
        listening_questions_total = self._validate_passage_section(
            cleaned_data,"Listening","listening"
        )
        passage_question_total = reading_questions_total + listening_questions_total

        if total and levels_sum != total:
            raise forms.ValidationError(
                f"Seviyelere göre girilen soru sayıları toplamı ({levels_sum}) "
                f"toplam soru sayısına ({total}) eşit olmalı."
            )
        

        if total and passage_question_total>total:
            raise forms.ValidationError(
                f"Passage'dan gelen soru sayısı ({passage_question_total}), "
                f"toplam soru sayısınu ({total}) aşamaz."
            )

        cleaned_data["level_counts"] = level_counts
        cleaned_data["passage_question_total"] = passage_question_total
        return cleaned_data

    def get_params(self):
        return {
            "name" : self.cleaned_data["name"].strip(),
            "total": self.cleaned_data["total"],
            "levels": self.cleaned_data["level_counts"],
            "tags": [tag.id for tag in self.cleaned_data["tags"]],
            "reading_passage_count": self.cleaned_data.get("reading_passage_count") or 0,
            "reading_questions_per_passage": self.cleaned_data.get("reading_questions_per_passage") or 0,
            "reading_questions_total" : self.cleaned_data.get("reading_questions_total") or 0,
            "listening_passage_count": self.cleaned_data.get("listening_passage_count") or 0,
            "listening_questions_per_passage": self.cleaned_data.get("listening_questions_per_passage") or 0,
            "listening_questions_total": self.cleaned_data.get("listening_questions_total") or 0, 
        }