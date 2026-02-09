from django.contrib import admin
from django.urls import path
from diario.views import EmotionsView

urlpatterns = [
    path('emotions/', EmotionsView.as_view(), name='emotions'),
]
