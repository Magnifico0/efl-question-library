from django.db import models

# Create your models here.
from accounts.models import Organization,User
from questions.models import Question

class Exam(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name= 'exams',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    name = models.CharField(
        max_length=100, blank=True
    )
    parameters = models.JSONField()
    questions = models.ManyToManyField(
        Question,
        related_name='exams'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ["-created_at"]

    def __str__(self):
        return f"Exam #{self.pk} - {self.teacher} - {self.created_at: %d-%m-%Y}"
    

class TeacherQuestionIndex(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete= models.CASCADE,
        related_name='question_index'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='used_by'

    )
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta: 
        #a question cannot go to a teacher for two times 
        unique_together = ("teacher", "question")

    def __str__(self):
        return f"{self.teacher} - {self.question} - ({self.used_at: %d-%m-%Y})"