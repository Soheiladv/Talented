from django.contrib import admin
from django.urls import path

from django.urls import path

from quiz_finder.views import QuizHomeView,TakeQuizView,generate_quiz_api

urlpatterns = [
    path('', QuizHomeView.as_view(), name='home'),
    path('quiz/', TakeQuizView.as_view(), name='take_quiz'),  # صفحه خالی آزمون
    path('api/generate-quiz/', generate_quiz_api, name='generate_quiz_api'),  # API برای تولید سوال
]


