from django.contrib import admin
from django.urls import path
from .views import historico_emocional
from diario import views
from diario.views import EmotionsView, homePageViews

urlpatterns = [

    path('homePage/', views.homePageViews.as_view(), name='homePage'), 
    path('home/', views.HomeView.as_view(), name='home'),
    path('emotions/', EmotionsView.as_view(), name='emotions'),
    path('salvar-emocao/', views.salvar_emocao, name="salvar_emocao"),
    path('sobre/', views.sobre.as_view(), name='sobre'),
    path('historico/', historico_emocional, name='historico')
]
