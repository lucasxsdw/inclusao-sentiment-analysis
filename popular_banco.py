import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# 1. Configura o ambiente do Django
# IMPORTANTE: Substitua 'config' pelo nome da pasta onde está o seu settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. Importa os modelos depois do setup
from django.contrib.auth import get_user_model
from accounts.models import Aluno
from diario.models import SessaoEmocional, Diario, Resposta, Pergunta

User = get_user_model()

def popular():
    nomes = ["Lucas Silva", "Ana Oliveira", "Bruno Santos", "Carla Costa", "Diego Lima", 
             "Fernanda Souza", "Gabriel Rocha", "Helena Neves", "Igor Gomes", "Juliana Ferraz"]

    deficiencias = ["tea", "baixa_visao", "surdez", "tdah", "dislexia", "outro"]
    emocoes = ['muito_feliz', 'feliz', 'neutro', 'triste', 'muito_triste', 'ansioso', 'irritado']

    print("🚀 Iniciando população de dados no Render...")

    # Garante que existe pelo menos uma pergunta para não dar erro
    pergunta_padrao = Pergunta.objects.first()
    if not pergunta_padrao:
        print("❌ Erro: Crie pelo menos uma Pergunta no Admin antes de rodar este script.")
        return

    for i in range(10):
        nome_completo = nomes[i]
        sufixo = str(random.randint(100, 999))
        username = nome_completo.lower().replace(" ", "") + sufixo
        email_fake = f"{username}@escola.com"
        
        if User.objects.filter(username=username).exists():
            continue

        try:
            # Cria Usuário
            user = User.objects.create_user(
                username=username,
                email=email_fake,
                password="SenhaTeste123@",
                first_name=nome_completo.split()[0],
                last_name=nome_completo.split()[1],
                tipo_usuario='aluno'
            )
            
            # Cria Perfil
            aluno = Aluno.objects.create(
                usuario=user,
                tipo_deficiencia=random.choice(deficiencias),
                necessidades_especificas="Acompanhamento pedagógico regular via sistema."
            )
            
            # Cria Histórico (últimos 10 dias)
            for d in range(10):
                data_aleatoria = timezone.now() - timedelta(days=d)
                emocao = random.choice(emocoes)
                
                sessao = SessaoEmocional.objects.create(
                    aluno=aluno,
                    emocao_selecionada=emocao
                )
                # Força a data retroativa no banco
                SessaoEmocional.objects.filter(id=sessao.id).update(data_criacao=data_aleatoria)
                
                diario = Diario.objects.create(
                    sessao_emocional=sessao,
                    mensagem_inicial_ia="Olá! Como você está hoje?"
                )
                
                Resposta.objects.create(
                    diario=diario,
                    texto_resposta=f"Hoje meu sentimento é {emocao}.",
                    pergunta=pergunta_padrao
                )
            print(f"✅ Aluno {nome_completo} e histórico criados.")
            
        except Exception as e:
            print(f"❌ Erro ao criar {nome_completo}: {e}")

if __name__ == "__main__":
    popular()
    print("\n✨ População concluída com sucesso!")