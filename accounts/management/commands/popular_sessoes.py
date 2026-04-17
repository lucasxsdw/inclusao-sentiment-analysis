import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
# Exemplo (ajuste conforme o seu projeto):
from diario.models import Diario, SessaoEmocional, Pergunta
# IMPORTANTE: Verifique se esses imports estão corretos conforme o seu projeto!
from accounts.models import Aluno
from diario.models import Diario, SessaoEmocional
from analise.models import Resposta, AnaliseResposta 

class Command(BaseCommand):
    help = 'Popula o banco com sessões aleatórias e gera dados perfeitos para o gráfico'

    def handle(self, *args, **kwargs):
        alunos = Aluno.objects.all()
        if not alunos.exists():
            self.stdout.write(self.style.ERROR('Nenhum aluno encontrado. Rode o popular_alunos primeiro.'))
            return

        # --- PARTE 2: GERAR DADOS COM SCORE PARA O GRÁFICO (1º Aluno) ---
        self.stdout.write('Gerando curva de evolução para o gráfico do primeiro aluno...')
        aluno_grafico = alunos.first()

        # 1. Buscamos a primeira pergunta cadastrada no banco de dados
        pergunta_padrao = Pergunta.objects.first()

        # Proteção: Se não houver pergunta, o script avisa e para.
        if not pergunta_padrao:
            self.stdout.write(self.style.ERROR('⚠️ Nenhuma "Pergunta" encontrada no banco. Crie pelo menos uma pergunta no Painel Admin antes de rodar!'))
            return

        historico_simulado = [
            {'dias_atras': 5, 'emocao': 'triste',  'score': 0.20, 'texto': 'Hoje foi um dia muito difícil, me senti isolado.'},
            {'dias_atras': 4, 'emocao': 'ansioso', 'score': 0.45, 'texto': 'Ainda estou preocupado, mas conversei com um amigo.'},
            {'dias_atras': 3, 'emocao': 'neutro',  'score': 0.60, 'texto': 'Um dia normal, consegui focar um pouco mais nas aulas.'},
            {'dias_atras': 2, 'emocao': 'feliz',   'score': 0.85, 'texto': 'Fui muito bem na atividade de hoje! Estou confiante.'},
            {'dias_atras': 1, 'emocao': 'feliz',   'score': 0.95, 'texto': 'Semana encerrada com chave de ouro, me sinto ótimo!'},
        ]

        hoje = timezone.now()

        for item in historico_simulado:
            data_sessao = hoje - timedelta(days=item['dias_atras'])
            
            sessao = SessaoEmocional.objects.create(
                aluno=aluno_grafico,
                emocao_selecionada=item['emocao']
            )
            SessaoEmocional.objects.filter(id=sessao.id).update(data_inicio=data_sessao)
            
            diario = Diario.objects.create(sessao_emocional=sessao)
            
            # 2. A CORREÇÃO ESTÁ AQUI: Incluímos a pergunta_padrao!
            resposta = Resposta.objects.create(
                diario=diario,
                pergunta=pergunta_padrao, 
                texto_resposta=item['texto']
            )
            
            AnaliseResposta.objects.create(
                resposta=resposta,
                sentimento_detectado=item['emocao'],
                score_sentimento=item['score']
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Sucesso! Gráfico e histórico populados perfeitamente para: {aluno_grafico.usuario.get_full_name()}'))