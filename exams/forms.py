from django import forms
from django.forms import formset_factory

from questions.models import Tag, Level


class PassageSlotForm(forms.Form):
    """
    Tek bir parça slotu: "bu parça X seviyesinden olsun ve Y soru versin".
    Şablonda 'Parça Ekle' butonuyla dinamik olarak çoğaltılır.
    """
    level = forms.ChoiceField(
        choices=[("", "Seviye seçin")] + list(Level.choices),
        required=False,
        label="Seviye",
        widget=forms.Select(attrs={"class": "form-select passage-slot-level"}),
    )
    question_count = forms.IntegerField(
        min_value=1,
        required=False,
        label="Soru Sayısı",
        widget=forms.NumberInput(attrs={
            "class": "form-control passage-slot-count",
            "min": 1,
        }),
    )

    def clean(self):
        cleaned = super().clean()
        level = cleaned.get("level")
        count = cleaned.get("question_count")

        if not level and not count:
            cleaned["_empty"] = True
            return cleaned

        if not level:
            raise forms.ValidationError("Seviye seçilmedi.")
        if not count:
            raise forms.ValidationError("Soru sayısı girilmedi.")

        cleaned["_empty"] = False
        return cleaned


PassageSlotFormSet = formset_factory(PassageSlotForm, extra=0, can_delete=False)


class ExamGenerationForm(forms.Form):
    """
    ModelForm değil, çünkü Exam.parameters JSON alanı doğrudan form
    alanlarına 1:1 karşılık gelmiyor. Parça slotları bu formda değil,
    ayrı PassageSlotFormSet içinde tutulur (reading/listening).
    """
    name = forms.CharField(
        required=False,
        label="Sınav Adı",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Boş bırakılırsa tarih otomatik atanır.",
        }),
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

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total")

        level_counts = {}
        for code, _ in Level.choices:
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

    @staticmethod
    def slots_from_formset(formset):
        slots = []
        for form in formset:
            if not form.cleaned_data or form.cleaned_data.get("_empty"):
                continue
            slots.append({
                "level": form.cleaned_data["level"],
                "question_count": form.cleaned_data["question_count"],
            })
        return slots

    def validate_against_slots(self, reading_slots, listening_slots):
        total = self.cleaned_data.get("total")
        level_counts = self.cleaned_data.get("level_counts", {})
        if not total:
            return

        demand = {}
        for slot in reading_slots + listening_slots:
            demand[slot["level"]] = demand.get(slot["level"], 0) + slot["question_count"]

        for level, needed in demand.items():
            quota = level_counts.get(level, 0)
            if needed > quota:
                self.add_error(
                    None,
                    f"{level} seviyesinde parçalardan {needed} soru istendi, ama bu "
                    f"seviye için ayrılan toplam soru sayısı {quota}.",
                )

        passage_total = sum(demand.values())
        if passage_total > total:
            self.add_error(
                None,
                f"Parçalardan gelen soru sayısı ({passage_total}), toplam soru "
                f"sayısını ({total}) aşamaz.",
            )

    def get_params(self, reading_slots, listening_slots):
        return {
            "name": (self.cleaned_data.get("name") or "").strip(),
            "total": self.cleaned_data["total"],
            "levels": self.cleaned_data["level_counts"],
            "tags": [tag.id for tag in self.cleaned_data["tags"]],
            "reading_passages": reading_slots,
            "listening_passages": listening_slots,
        }