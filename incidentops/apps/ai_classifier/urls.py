from django.urls import path
from . import views

app_name = 'ai_classifier'

urlpatterns = [
    path('suggest/', views.suggest_view, name='suggest'),
]