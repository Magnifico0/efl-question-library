from django.urls import path 
from questions.views import QuestionCreateView,QuestionListView,QuestionUpdateView,PassageCreateView,PassageDetailView

app_name = "questions"

urlpatterns = [
    path("",QuestionListView.as_view(), name="list"),
    path("add/",QuestionCreateView.as_view(),name="create"),
    path("<int:pk>/edit/",QuestionUpdateView.as_view(), name= "update"),
    path("passages/add/",PassageCreateView.as_view(),name="passage_create"),
    path("pasages/<int:pk>/",PassageDetailView.as_view(),name="passage_detail"),

]