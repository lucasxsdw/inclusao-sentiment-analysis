from django.urls import path
from . import views
from .views import historico_emocional



urlpatterns = [
    path('chat/', views.enviar_desabafo, name='enviar_desabafo'),
    path('painel/', views.painel_napne, name='painel'),
    path('painel/aluno/<int:aluno_id>/', views.perfil_aluno_napne, name='perfil_aluno_napne'),
    path('alunos/', views.listar_alunos, name='alunos'),
    path('historico/', historico_emocional, name='historico'),
    path('estatisticas/', views.estatisticas_gerais, name='estatisticas_gerais'),
    path('configuracoes/', views.configuracoes_servidor, name='configuracoes_servidor'),
]