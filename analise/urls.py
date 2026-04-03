from django.urls import path
from . import views


urlpatterns = [
    path('chat/', views.enviar_desabafo, name='enviar_desabafo'),
    path('painel/', views.painel_napne, name='painel'),
    path('painel/aluno/<int:aluno_id>/', views.perfil_aluno_napne, name='perfil_aluno_napne'),
    path('alunos/', views.listar_alunos, name='alunos'),

]