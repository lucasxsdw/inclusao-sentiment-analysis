from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.enviar_desabafo, name='enviar_desabafo'),
]