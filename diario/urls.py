from django.contrib import admin
from django.urls import path
from diario import views
from diario.views import EmotionsView
from diario.views import ChatView

urlpatterns = [
    path('emotions/', EmotionsView.as_view(), name='emotions'),
    path("salvar-emocao/", views.salvar_emocao, name="salvar_emocao"),
    path('chat/<int:diario_id>/', ChatView.as_view(), name='chat'),
]
