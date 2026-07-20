from django.contrib import admin

# Register your models here.
#not have to actually just to make simple while debugging 
from exams.models import Exam, TeacherQuestionIndex

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["id","teacher","organization","created_at","question_count"]
    list_filter = ["organization","created_at"]
    search_fields = ["teacher__username","teacher__first_name","teacher__lastname","organization"]
    readonly_fields = ["created_at"]

    def question_count(self,obj):
        return obj.questions.count()
    question_count.short_description= "Soru Sayısı"

@admin.register(TeacherQuestionIndex)
class TeacherQuestionIndexAdmin(admin.ModelAdmin):
    list_display = ["teacher", "question", "used_at"]
    list_filter = ["used_at"]
    search_fields = ["teacher__username", "question__text"]