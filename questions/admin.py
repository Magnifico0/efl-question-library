from django.contrib import admin
from questions.models import TagCategory,Tag,Question,Choice
# Register your models here.

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4 
    fields = ["text","is_correct"]


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name","category"]
    list_filter = ["category"]
    search_fields = ["name","category"]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["level","text_preview","is_active","organization","created_by"]
    list_filter = ["level","is_active", "organization","created_by"]
    search_fields = ["text"]
    inlines = [ChoiceInline]

    def text_preview(self,obj):
        return obj.text[:50]
    text_preview.short_description = "Soru"

