from django.contrib import admin
from django.urls import path
from diario import views
from diario.views import EmotionsView

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='home'),
    path('emotions/', EmotionsView.as_view(), name='emotions'),
    path("salvar-emocao/", views.salvar_emocao, name="salvar_emocao"),
]
