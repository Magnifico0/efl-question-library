from django.urls import path 
from questions.views import QuestionCreateView,QuestionListView,QuestionUpdateView

app_name = "questions"

urlpatterns = [
    path("",QuestionListView.as_view(), name="list"),
    path("add/",QuestionCreateView.as_view(),name="create"),
    path("<int:pk>/edit/",QuestionUpdateView.as_view(), name= "update")
]